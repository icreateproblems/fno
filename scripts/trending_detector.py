"""
Trending topics detection system.
Identifies viral/trending stories for priority posting.
"""
import os
import sys
import requests
from typing import List, Dict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger

logger = get_logger(__name__)

class TrendingDetector:
    """Detect trending topics and viral stories"""
    
    def __init__(self):
        self.serper_key = os.getenv("SERPER_API_KEY")
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")  # Optional
    
    def is_trending(self, headline: str, category: str = "general") -> Dict:
        """
        Determine if topic is trending.
        
        Returns:
            {
                'is_trending': bool,
                'trend_score': int (0-100),
                'trending_keywords': List[str],
                'reasoning': str
            }
        """
        logger.info(f"🔥 Checking trending status: {headline[:60]}...")
        
        signals = []
        
        # Signal 1: Google Trends volume
        google_score = self._check_google_trends(headline)
        signals.append(('google', google_score))
        
        # Signal 2: News coverage density
        news_score = self._check_news_coverage(headline)
        signals.append(('news', news_score))
        
        # Signal 3: Social media mentions (if Twitter API available)
        if self.twitter_bearer:
            social_score = self._check_social_mentions(headline)
            signals.append(('social', social_score))
        
        # Calculate overall trend score
        if signals:
            trend_score = int(sum(score for _, score in signals) / len(signals))
        else:
            trend_score = 0
        
        is_trending = trend_score >= 70
        
        result = {
            'is_trending': is_trending,
            'trend_score': trend_score,
            'trending_keywords': self._extract_trending_keywords(headline),
            'reasoning': f"Trend score: {trend_score}/100 from {len(signals)} signals"
        }
        
        logger.info(
            f"{'🔥 TRENDING' if is_trending else '📰 Normal'}: "
            f"{trend_score}/100"
        )
        
        return result
    
    def _check_google_trends(self, headline: str) -> int:
        """Check if topic has high Google search volume"""
        # TODO: Integrate Google Trends API (requires setup)
        # For now, return baseline score
        return 50
    
    def _check_news_coverage(self, headline: str) -> int:
        """Check news coverage density across sources"""
        
        if not self.serper_key:
            return 50
        
        try:
            response = requests.post(
                "https://google.serper.dev/news",
                headers={
                    "X-API-KEY": self.serper_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": headline[:100],
                    "num": 20,
                    "tbs": "qdr:h"  # Last hour
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("news", [])
                
                # More recent coverage = higher trend score
                num_results = len(results)
                
                if num_results >= 15:
                    return 100  # Viral
                elif num_results >= 10:
                    return 90  # Very trending
                elif num_results >= 5:
                    return 75  # Trending
                elif num_results >= 2:
                    return 60  # Some buzz
                else:
                    return 40  # Low coverage
            
            return 50
            
        except Exception as e:
            logger.error(f"News coverage check failed: {e}")
            return 50
    
    def _check_social_mentions(self, headline: str) -> int:
        """Check social media mentions (Twitter)"""
        # TODO: Implement Twitter API v2 search
        # Requires Twitter API credentials
        return 50
    
    def _extract_trending_keywords(self, headline: str) -> List[str]:
        """Extract likely trending keywords from headline"""
        
        # Common trending indicators
        trending_terms = [
            'breaking', 'just in', 'developing', 'exclusive',
            'viral', 'trending', 'record', 'first time',
            'historic', 'unprecedented', 'emergency', 'crisis'
        ]
        
        headline_lower = headline.lower()
        found_terms = [term for term in trending_terms if term in headline_lower]
        
        return found_terms


def prioritize_trending_stories(supabase) -> List[Dict]:
    """
    Re-prioritize story queue based on trending status.
    Trending stories get posted first.
    """
    detector = TrendingDetector()
    
    # Get unposted validated stories
    stories = supabase.table("stories").select(
        "*"
    ).eq(
        "is_validated", True
    ).eq(
        "posted", False
    ).order(
        "published_at", desc=True
    ).limit(20).execute().data
    
    # Score each story for trending
    scored_stories = []
    for story in stories:
        trend_result = detector.is_trending(
            story['headline'],
            story.get('category', 'general')
        )
        
        story['trend_score'] = trend_result['trend_score']
        story['is_trending'] = trend_result['is_trending']
        scored_stories.append(story)
    
    # Sort by trend score (highest first)
    scored_stories.sort(key=lambda x: x['trend_score'], reverse=True)
    
    # Log priority order
    logger.info("📊 Story Priority Queue:")
    for i, story in enumerate(scored_stories[:5], 1):
        trend_emoji = "🔥" if story['is_trending'] else "📰"
        logger.info(
            f"  {i}. {trend_emoji} [{story['trend_score']}/100] "
            f"{story['headline'][:50]}..."
        )
    
    return scored_stories
