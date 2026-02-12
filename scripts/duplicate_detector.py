"""
Advanced duplicate detection using semantic similarity.
Prevents posting the same story with different headlines.
"""
import os
import sys
from typing import List, Dict, Tuple
import hashlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger
from app.config import GROQ_API_KEY
from app.api_key_manager import get_groq_key
import requests

logger = get_logger(__name__)

USE_KEY_ROTATION = True

class DuplicateDetector:
    """Detect semantically similar stories to prevent duplicates"""
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.model = "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.similarity_threshold = 0.75  # 75% similar = duplicate
    
    def is_duplicate(self, new_headline: str, new_description: str, hours_lookback: int = 24) -> Tuple[bool, str]:
        """
        Check if story is duplicate of recently posted content.
        
        Returns:
            (is_duplicate: bool, reason: str)
        """
        logger.info(f"🔍 Checking duplicates: {new_headline[:60]}...")
        
        # Get recent stories from database
        cutoff_time = (datetime.now() - timedelta(hours=hours_lookback)).isoformat()
        
        recent_stories = self.supabase.table("stories").select(
            "headline, description, posted_at"
        ).eq(
            "posted", True
        ).gte(
            "posted_at", cutoff_time
        ).execute().data
        
        if not recent_stories:
            logger.info("✓ No recent stories to compare - not duplicate")
            return False, "No recent content"
        
        logger.info(f"Comparing against {len(recent_stories)} recent stories")
        
        # Check each recent story
        for story in recent_stories:
            similarity = self._calculate_similarity(
                new_headline,
                new_description,
                story['headline'],
                story.get('description', '')
            )
            
            if similarity >= self.similarity_threshold:
                reason = (
                    f"Too similar ({similarity:.0%}) to: "
                    f"{story['headline'][:50]}..."
                )
                logger.warning(f"❌ Duplicate detected: {reason}")
                return True, reason
        
        logger.info("✓ Not a duplicate")
        return False, "Unique content"
    
    def _calculate_similarity(
        self,
        headline1: str,
        desc1: str,
        headline2: str,
        desc2: str
    ) -> float:
        """Calculate semantic similarity using AI"""
        
        prompt = f"""Compare these two news stories and rate their similarity.

STORY 1:
Headline: {headline1}
Description: {desc1[:200]}

STORY 2:
Headline: {headline2}
Description: {desc2[:200]}

Are these the SAME story (just worded differently)?

Consider:
- Same event/topic?
- Same key facts?
- Same time period?
- Same people/organizations involved?

SCORING:
- 1.0 = Identical story (same event, different wording)
- 0.8-0.9 = Very similar (same story, minor details differ)
- 0.5-0.7 = Related but different angles
- 0.3-0.4 = Same topic, different stories
- 0.0-0.2 = Completely different

Respond with ONLY a number between 0.0 and 1.0
"""

        try:
            if USE_KEY_ROTATION:
                api_key = get_groq_key()
            else:
                api_key = GROQ_API_KEY
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 10,
                },
                timeout=15,
            )
            response.raise_for_status()
            
            result_text = response.json()['choices'][0]['message']['content'].strip()
            
            # Extract number
            import re
            match = re.search(r'0\.\d+|1\.0', result_text)
            if match:
                similarity = float(match.group())
                logger.debug(f"Similarity score: {similarity:.2f}")
                return similarity
            
            # Fallback: simple text overlap
            return self._simple_overlap(headline1, headline2)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            # Fallback to simple method
            return self._simple_overlap(headline1, headline2)
    
    def _simple_overlap(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity (fallback)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


def check_duplicate_before_posting(
    supabase,
    headline: str,
    description: str,
    hours_lookback: int = 24
) -> Tuple[bool, str]:
    """
    Check if story is duplicate before posting.
    Returns (is_duplicate, reason)
    """
    detector = DuplicateDetector(supabase)
    return detector.is_duplicate(headline, description, hours_lookback)
