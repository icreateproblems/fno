"""
Random Posting Scheduler - Makes posting patterns unpredictable and human-like
Avoids detection as automated bot by Instagram and CI/CD platforms
"""
import os
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path

class RandomScheduler:
    """
    Manages random posting intervals to appear human-like.
    
    Key features:
    - Variable intervals (20-90 minutes between posts)
    - Avoids predictable patterns
    - Respects daily limits (30-40 posts/day)
    - Adds "drift" to simulate human behavior
    - Stores state to coordinate across CI/CD runs
    """
    
    def __init__(self, 
                 min_interval_minutes: int = 20,
                 max_interval_minutes: int = 90,
                 daily_target_min: int = 30,
                 daily_target_max: int = 40,
                 state_file: str = "scheduler_state.json"):
        """
        Initialize random scheduler.
        
        Args:
            min_interval_minutes: Minimum time between posts (20 min)
            max_interval_minutes: Maximum time between posts (90 min)
            daily_target_min: Minimum posts per day (30)
            daily_target_max: Maximum posts per day (40)
            state_file: File to store scheduler state
        """
        self.min_interval = min_interval_minutes
        self.max_interval = max_interval_minutes
        self.daily_target_min = daily_target_min
        self.daily_target_max = daily_target_max
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load scheduler state from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load state: {e}")
        
       # Default state
        return {
            "last_post_time": None,
            "next_post_time": None,
            "posts_today": 0,
            "last_reset_date": None,
            "daily_target": random.randint(self.daily_target_min, self.daily_target_max)
        }
    
    def _save_state(self):
        """Save scheduler state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def _reset_daily_counter(self):
        """Reset daily counter if it's a new day."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        if self.state.get("last_reset_date") != today:
            self.state["posts_today"] = 0
            self.state["last_reset_date"] = today
            # Randomize daily target for unpredictability
            self.state["daily_target"] = random.randint(self.daily_target_min, self.daily_target_max)
            self._save_state()
    
    def _calculate_next_post_time(self) -> datetime:
        """Calculate next random post time with human-like variance."""
        now = datetime.now()
        
        # Base interval with randomness
        base_interval = random.uniform(self.min_interval, self.max_interval)
        
        # Add "drift" - humans don't post at exact intervals
        drift = random.gauss(0, 5)  # Normal distribution, ±5 min drift
        interval_minutes = max(self.min_interval, base_interval + drift)
        
        # Time-of-day adjustments (humans post more during active hours)
        hour = now.hour
        if 22 <= hour or hour < 6:
            # Less posting at night (1.5x longer intervals)
            interval_minutes *= 1.5
        elif 10 <= hour < 14 or 18 <= hour < 21:
            # More posting during peak hours (0.8x shorter intervals)
            interval_minutes *= 0.8
        
        next_time = now + timedelta(minutes=interval_minutes)
        return next_time
    
    def should_post_now(self) -> bool:
        """
        Determine if we should post now based on random schedule.
        
        Returns:
            True if it's time to post, False otherwise
        """
        self._reset_daily_counter()
        now = datetime.now()
        
        # Check daily limit
        if self.state["posts_today"] >= self.state["daily_target"]:
            print(f"✓ Daily target reached ({self.state['posts_today']}/{self.state['daily_target']})")
            return False
        
        # First post of the day
        if self.state["next_post_time"] is None:
            self.state["next_post_time"] = self._calculate_next_post_time().isoformat()
            self._save_state()
            return True
        
        # Check if it's time for next post
        next_post_time = datetime.fromisoformat(self.state["next_post_time"])
        
        if now >= next_post_time:
            return True
        
        # Not time yet
        time_remaining = (next_post_time - now).total_seconds() / 60
        print(f"⏳ Next post in {time_remaining:.1f} minutes")
        return False
    
    def mark_post_completed(self):
        """Mark that a post was successfully completed."""
        now = datetime.now()
        self.state["last_post_time"] = now.isoformat()
        self.state["posts_today"] = self.state.get("posts_today", 0) + 1
        self.state["next_post_time"] = self._calculate_next_post_time().isoformat()
        self._save_state()
        
        print(f"✓ Post completed. Today: {self.state['posts_today']}/{self.state['daily_target']}")
        
        next_post = datetime.fromisoformat(self.state["next_post_time"])
        minutes_until_next = (next_post - now).total_seconds() / 60
        print(f"⏰ Next post scheduled in ~{minutes_until_next:.0f} minutes")
    
    def get_stats(self) -> Dict:
        """Get current scheduler statistics."""
        self._reset_daily_counter()
        
        stats = {
            "posts_today": self.state["posts_today"],
            "daily_target": self.state["daily_target"],
            "last_post_time": self.state.get("last_post_time"),
            "next_post_time": self.state.get("next_post_time"),
            "posts_remaining": self.state["daily_target"] - self.state["posts_today"]
        }
        
        if self.state.get("next_post_time"):
            next_post = datetime.fromisoformat(self.state["next_post_time"])
            now = datetime.now()
            stats["minutes_until_next"] = max(0, (next_post - now).total_seconds() / 60)
        
        return stats


def should_attempt_post() -> bool:
    """
    Convenience function to check if we should attempt to post.
    
    Usage in posting scripts:
        from app.random_scheduler import should_attempt_post
        
        if should_attempt_post():
            # Proceed with posting logic
            ...
    """
    scheduler = RandomScheduler()
    return scheduler.should_post_now()


def mark_successful_post():
    """
    Convenience function to mark post as completed.
    
    Usage after successful post:
        from app.random_scheduler import mark_successful_post
        mark_successful_post()
    """
    scheduler = RandomScheduler()
    scheduler.mark_post_completed()


if __name__ == "__main__":
    # Test the scheduler
    scheduler = RandomScheduler()
    print("=" * 60)
    print("Random Posting Scheduler Test")
    print("=" * 60)
    
    stats = scheduler.get_stats()
    print(f"\n📊 Current Stats:")
    print(f"  Posts today: {stats['posts_today']}/{stats['daily_target']}")
    print(f"  Posts remaining: {stats['posts_remaining']}")
    
    if stats.get('minutes_until_next'):
        print(f"  Next post in: {stats['minutes_until_next']:.1f} minutes")
    
    print(f"\n🎲 Should post now? {scheduler.should_post_now()}")
