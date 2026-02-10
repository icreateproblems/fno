"""
AI Content Monitor - Intelligent decision system for publishing news

Uses Groq/Claude to evaluate if content is:
- Ethical and appropriate
- Engaging and interesting
- Novel and not repetitive
- Suitable for Instagram audience
- Trending or newsworthy

Makes final publishing decision based on AI analysis.
"""
import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger
from app.config import GROQ_API_KEY

try:
    from app.api_key_manager import get_groq_key, mark_groq_key_failed
    USE_KEY_ROTATION = True
except ImportError:
    USE_KEY_ROTATION = False

logger = get_logger(__name__)


class AIContentMonitor:
    """Intelligent content decision system powered by Groq"""
    
    def __init__(self):
        if USE_KEY_ROTATION:
            self.api_key = None  # Will be fetched per request
        else:
            self.api_key = GROQ_API_KEY
        self.model = "llama-3.1-8b-instant"  # Current stable small model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def evaluate_content(self, headline: str, description: str, category: str, source: str) -> dict:
        """
        Evaluate content using AI to decide if it should be published.
        
        Returns:
            {
                'should_publish': bool,
                'confidence': float (0-1),
                'score': int (0-100),
                'reasoning': str,
                'ethics_score': int,
                'engagement_score': int,
                'novelty_score': int,
                'trending_score': int
            }
        """
        try:
            prompt = self._build_evaluation_prompt(headline, description, category, source)
            
            logger.info(f"🤖 AI evaluating: {headline[:60]}...")
            
            if USE_KEY_ROTATION:
                api_key = get_groq_key()
            else:
                api_key = self.api_key
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 600,
                },
                timeout=30,
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            logger.debug(f"AI Response: {response_text}")
            
            # Parse AI response
            decision = self._parse_ai_response(response_text, headline)
            return decision
            
        except requests.exceptions.HTTPError as he:
            logger.error(f"❌ API HTTP Error: {he}")
            if he.response.status_code in (429, 401) and USE_KEY_ROTATION:
                mark_groq_key_failed(api_key)
            try:
                error_detail = he.response.json()
                logger.error(f"Error details: {error_detail}")
            except:
                logger.error(f"Response text: {he.response.text}")
            # Fallback: default to not publishing if API fails
            return {
                'should_publish': False,
                'confidence': 0.3,
                'score': 0,
                'reasoning': f'AI API error: {str(he)}',
                'ethics_score': 0,
                'engagement_score': 0,
                'novelty_score': 0,
                'trending_score': 0
            }
        except Exception as e:
            logger.error(f"❌ AI evaluation failed: {e}")
            # Fallback: default to not publishing if AI fails
            return {
                'should_publish': False,
                'confidence': 0.3,
                'score': 0,
                'reasoning': f'AI system error: {str(e)}',
                'ethics_score': 0,
                'engagement_score': 0,
                'novelty_score': 0,
                'trending_score': 0
            }
    
    def _build_evaluation_prompt(self, headline: str, description: str, category: str, source: str) -> str:
        """Build the evaluation prompt for the AI"""
        
        return f"""You are an expert content moderator for a news Instagram account (@fastnewsorg). 
Your job is to decide if this news story should be published.

STORY TO EVALUATE:
- Headline: {headline}
- Description: {description}
- Category: {category}
- Source: {source}

EVALUATE THIS STORY ON:

1. **ETHICS** (0-100): Is it appropriate? Any misinformation? Biased reporting? Offensive content?
   - 90-100: Perfectly balanced, factual, non-offensive
   - 70-89: Generally good, minor concerns
   - 50-69: Some concerns but publishable
   - Below 50: Problematic content

2. **ENGAGEMENT** (0-100): Will Instagram audience find it interesting/shocking/important?
   - 90-100: Trending, highly engaging, must-see
   - 70-89: Very engaging, good for engagement
   - 50-69: Moderately interesting
   - Below 50: Boring or niche

3. **NOVELTY** (0-100): Is this fresh news or old/repetitive?
   - 90-100: Breaking news, completely fresh
   - 70-89: Recent and relevant
   - 50-69: Somewhat recent
   - Below 50: Old or repetitive

4. **TRENDING** (0-100): Is this trending or newsworthy right now?
   - 90-100: Major trending topic
   - 70-89: Trending in news cycle
   - 50-69: Somewhat relevant
   - Below 50: Not trending

RESPOND IN THIS EXACT JSON FORMAT (no other text):
{{
    "should_publish": true/false,
    "confidence": 0.0-1.0,
    "ethics_score": 0-100,
    "engagement_score": 0-100,
    "novelty_score": 0-100,
    "trending_score": 0-100,
    "overall_score": 0-100,
    "reasoning": "Brief explanation of why to publish or not"
}}

Remember:
- We want ENGAGING and ETHICAL content
- Focus on global news, politics, tech, business, events
- Minimum acceptable score: 50/100
- Prefer high engagement (70+) stories
- Ethics is non-negotiable (must be 50+)
"""
    
    def _parse_ai_response(self, response_text: str, headline: str) -> dict:
        """Parse the JSON response from AI"""
        
        try:
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"Could not find JSON in response: {response_text[:200]}")
                return {
                    'should_publish': False,
                    'confidence': 0.2,
                    'score': 0,
                    'reasoning': 'Could not parse AI response',
                    'ethics_score': 0,
                    'engagement_score': 0,
                    'novelty_score': 0,
                    'trending_score': 0
                }
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Validate and construct response
            decision = {
                'should_publish': data.get('should_publish', False),
                'confidence': min(1.0, max(0.0, data.get('confidence', 0.5))),
                'score': data.get('overall_score', 50),
                'ethics_score': data.get('ethics_score', 50),
                'engagement_score': data.get('engagement_score', 50),
                'novelty_score': data.get('novelty_score', 50),
                'trending_score': data.get('trending_score', 50),
                'reasoning': data.get('reasoning', 'No reasoning provided')
            }
            
            # Apply publishing rules
            if decision['ethics_score'] < 40:
                decision['should_publish'] = False
                decision['reasoning'] = f"Ethics score too low ({decision['ethics_score']}/100)"
            elif decision['score'] < 45:
                decision['should_publish'] = False
                decision['reasoning'] = f"Overall score too low ({decision['score']}/100)"
            
            logger.info(f"📊 AI Decision:")
            logger.info(f"   Publish: {decision['should_publish']}")
            logger.info(f"   Score: {decision['score']}/100 (Ethics: {decision['ethics_score']}, Engagement: {decision['engagement_score']}, Novelty: {decision['novelty_score']}, Trending: {decision['trending_score']})")
            logger.info(f"   Reasoning: {decision['reasoning']}")
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response was: {response_text}")
            return {
                'should_publish': False,
                'confidence': 0.1,
                'score': 0,
                'reasoning': f'JSON parse error: {str(e)}',
                'ethics_score': 0,
                'engagement_score': 0,
                'novelty_score': 0,
                'trending_score': 0
            }


def should_publish_ai(headline: str, description: str, category: str = "general", source: str = "unknown") -> tuple:
    """
    Quick function to evaluate if content should be published.
    
    Returns:
        (should_publish: bool, score: int, reasoning: str)
    """
    monitor = AIContentMonitor()
    decision = monitor.evaluate_content(headline, description, category, source)
    
    return (
        decision['should_publish'],
        decision['score'],
        decision['reasoning']
    )


if __name__ == "__main__":
    # Test the monitor
    print("=" * 70)
    print("🤖 AI CONTENT MONITOR TEST")
    print("=" * 70)
    
    test_stories = [
        {
            "headline": "Bitcoin Reaches All-Time High Amid Global Market Shift",
            "description": "Cryptocurrency surges past $100,000 as institutional investors increase holdings",
            "category": "tech",
            "source": "Reuters"
        },
        {
            "headline": "New Cancer Treatment Shows 90% Success Rate in Clinical Trials",
            "description": "Revolutionary therapy approved for Phase 3 human trials, offers hope for thousands",
            "category": "health",
            "source": "Medical News Today"
        },
        {
            "headline": "Political Figure X Does Mundane Task",
            "description": "Politician seen walking down street in ordinary clothing",
            "category": "politics",
            "source": "Tabloid"
        }
    ]
    
    monitor = AIContentMonitor()
    
    for story in test_stories:
        print(f"\n📰 Story: {story['headline']}")
        decision = monitor.evaluate_content(
            story['headline'],
            story['description'],
            story['category'],
            story['source']
        )
        print(f"   Should Publish: {decision['should_publish']}")
        print(f"   Score: {decision['score']}/100")
        print(f"   Reasoning: {decision['reasoning']}")
