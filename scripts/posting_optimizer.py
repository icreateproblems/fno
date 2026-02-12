"""
ML-based posting time optimization.
Learns from engagement data to post when audience is most active.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger

logger = get_logger(__name__)

class PostingOptimizer:
    """Optimize posting times based on historical engagement"""
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.engagement_cache_file = "engagement_data.json"
    
    def get_optimal_posting_time(self, category: str = "general") -> Tuple[int, int]:
        """
        Get optimal posting hour based on historical data.
        
        Returns:
            (hour, minute) for best engagement
        """
        engagement_data = self._load_engagement_data()
        
        if not engagement_data:
            # Default to peak hours (9 AM and 6 PM Nepal time)
            return (9, 0) if datetime.now().hour < 12 else (18, 0)
        
        # Find hour with highest average engagement
        best_hour = max(
            engagement_data.items(),
            key=lambda x: x[1]['avg_engagement']
        )[0]
        
        # Add some randomness to avoid patterns
        import random
        minute = random.randint(0, 45)
        
        logger.info(f"📊 Optimal posting time: {best_hour}:{minute:02d}")
        return (int(best_hour), minute)
    
    def _load_engagement_data(self) -> Dict:
        """Load historical engagement data"""
        
        if os.path.exists(self.engagement_cache_file):
            try:
                with open(self.engagement_cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Calculate from database
        return self._calculate_engagement_by_hour()
    
    def _calculate_engagement_by_hour(self) -> Dict:
        """Calculate average engagement per hour from posting history"""
        
        # Get posts from last 30 days
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        
        try:
            posts = self.supabase.table("posting_history").select(
                "created_at, engagement_rate"
            ).gte(
                "created_at", cutoff
            ).eq(
                "success", True
            ).execute().data
            
            # Group by hour
            hour_data = {}
            for post in posts:
                try:
                    posted_time = datetime.fromisoformat(post['created_at'])
                    hour = posted_time.hour
                    
                    if hour not in hour_data:
                        hour_data[hour] = {'total': 0, 'count': 0}
                    
                    engagement = post.get('engagement_rate', 0)
                    hour_data[hour]['total'] += engagement
                    hour_data[hour]['count'] += 1
                except:
                    continue
            
            # Calculate averages
            result = {}
            for hour, data in hour_data.items():
                result[str(hour)] = {
                    'avg_engagement': data['total'] / data['count'] if data['count'] > 0 else 0,
                    'post_count': data['count']
                }
            
            # Cache results
            with open(self.engagement_cache_file, 'w') as f:
                json.dump(result, f)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement data: {e}")
            return {}
    
    def should_post_now(self) -> Tuple[bool, str]:
        """
        Intelligent decision on whether to post right now.
        Considers: time of day, recent posts, engagement patterns
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Load optimal hours
        engagement_data = self._load_engagement_data()
        
        if not engagement_data:
            # No data - use heuristics
            # Don't post late night (1 AM - 6 AM)
            if 1 <= current_hour < 6:
                return False, "Late night - low engagement hours"
            
            # Prefer morning (7-10 AM) and evening (5-9 PM)
            if (7 <= current_hour <= 10) or (17 <= current_hour <= 21):
                return True, "Peak hours"
            
            # Random chance during other hours
            import random
            if random.random() < 0.6:
                return True, "Active hours"
            else:
                return False, "Lower engagement hour"
        
        # Use ML-based decision
        current_hour_data = engagement_data.get(str(current_hour), {})
        avg_engagement = current_hour_data.get('avg_engagement', 0)
        
        # Calculate threshold (mean engagement across all hours)
        all_engagements = [
            data.get('avg_engagement', 0)
            for data in engagement_data.values()
        ]
        mean_engagement = sum(all_engagements) / len(all_engagements) if all_engagements else 0
        
        # Post if current hour is above average
        if avg_engagement >= mean_engagement:
            return True, f"Good engagement hour ({avg_engagement:.1f}% vs {mean_engagement:.1f}% avg)"
        else:
            # Still post with some probability to gather data
            import random
            if random.random() < 0.3:
                return True, "Exploring for data"
            else:
                return False, f"Below average engagement hour ({avg_engagement:.1f}% vs {mean_engagement:.1f}%)"
