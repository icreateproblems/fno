"""
AI-based content relevance scoring with diversity controls.
Determines if a story is interesting enough to post while preventing echo chambers.
"""
import os
import sys
import requests
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.diversity import DiversityManager

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def score_story_relevance(headline: str, description: str = "", category: str = "general", source: str = "", apply_diversity: bool = True) -> dict:
    """
    Score a story for relevance/interestingness (0-100).
    Applies diversity penalties to prevent echo chambers.
    High score = post it
    Low score = skip it (likely clickbait or low-quality)
    """
    if not GROQ_API_KEY:
        # Default: moderate confidence if no API
        return {
            "score": 50,
            "diversity_penalty": 0,
            "reason": "No API available - using default score",
            "publish": True,
            "success": False
        }

    prompt = f"""Analyze this news story for quality and public interest.
Score it 0-100 where:
- 90-100: Breaking news, important events, major incidents
- 70-89: Significant developments, important announcements  
- 50-69: Moderate interest, general news
- 30-49: Low interest, minor updates
- 0-29: Clickbait, trivial, spam

Return ONLY valid JSON:
{{"score": NUMBER, "reason": "SHORT reason (max 10 words)"}}

Headline: {headline}
Description: {description}
Category: {category}
"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,  # More consistent scoring
                "max_tokens": 100,
            },
            timeout=10,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()

        # Extract JSON
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            import json
            json_str = text[json_start:json_end]
            data = json.loads(json_str)
            base_score = int(data.get("score", 50))
            reason = data.get("reason", "")
            
            # Apply diversity penalty if enabled
            diversity_penalty = 0
            if apply_diversity and SUPABASE_URL and SUPABASE_KEY:
                try:
                    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    dm = DiversityManager(supabase)
                    diversity_penalty = dm.calculate_diversity_penalty(headline, description, source, category)
                    final_score = max(0, base_score - diversity_penalty)  # Don't go below 0
                except Exception as e:
                    print(f"Diversity check failed: {e}")
                    final_score = base_score
            else:
                final_score = base_score
            
            # Publish if score >= 50 after diversity adjustment
            return {
                "score": final_score,
                "base_score": base_score,
                "diversity_penalty": diversity_penalty,
                "reason": reason,
                "publish": final_score >= 50,
                "success": True
            }
    
    except Exception as e:
        print(f"Scoring error: {e}")
    
    # Fallback: publish everything
    return {
        "score": 50,
        "diversity_penalty": 0,
        "reason": "API error - publishing anyway",
        "publish": True,
        "success": False
    }


def should_publish(headline: str, description: str = "", category: str = "general", source: str = "") -> tuple:
    """
    Returns: (should_publish: bool, final_score: int, reason: str)
    """
    result = score_story_relevance(headline, description, category, source)
    
    # Include diversity info in reason if penalized
    reason = result["reason"]
    if result.get("diversity_penalty", 0) > 0:
        reason += f" (-{result['diversity_penalty']} diversity penalty)"
    
    return result["publish"], result["score"], reason


if __name__ == "__main__":
    # Test scoring
    test_stories = [
        ("Breaking: Major earthquake hits Japan", "A 7.2 magnitude earthquake...", "general", "BBC"),
        ("Celebrity wears new dress to event", "Famous actor wore...", "general", "Entertainment"),
        ("Stock market hits all-time high", "Markets surge as...", "financial", "CNBC"),
        ("Venezuela crisis deepens", "Political turmoil continues...", "general", "Reuters"),
    ]
    
    print("Testing story relevance scoring with diversity:\n")
    for headline, desc, cat, src in test_stories:
        publish, score, reason = should_publish(headline, desc, cat, src)
        status = "✓ POST" if publish else "✗ SKIP"
        print(f"{status} [{score}/100] {headline[:50]}")
        print(f"   Reason: {reason}\n")
