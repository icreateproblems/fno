"""
Real-time throughput monitoring for 2/hour target.
Shows if we're meeting posting goals.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
from app.logger import get_logger

logger = get_logger(__name__)

def check_throughput():
    """Check if we're meeting 2 posts/hour target"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    now = datetime.now()
    # Last hour
    hour_ago = (now - timedelta(hours=1)).isoformat()
    posts_last_hour = supabase.table("posting_history").select(
        "id"
    ).gte("created_at", hour_ago).eq("success", True).execute().data
    # Last 24 hours
    day_ago = (now - timedelta(hours=24)).isoformat()
    posts_last_day = supabase.table("posting_history").select(
        "id"
    ).gte("created_at", day_ago).eq("success", True).execute().data
    # Today so far
    today_start = now.replace(hour=0, minute=0, second=0).isoformat()
    posts_today = supabase.table("posting_history").select(
        "id"
    ).gte("created_at", today_start).eq("success", True).execute().data
    # Calculate rates
    posts_per_hour_actual = len(posts_last_hour)
    posts_per_day_actual = len(posts_last_day)
    posts_today_count = len(posts_today)
    # Targets
    TARGET_PER_HOUR = 2
    TARGET_PER_DAY = 48
    # Status
    hour_status = "✅" if posts_per_hour_actual >= TARGET_PER_HOUR else "⚠️"
    day_status = "✅" if posts_per_day_actual >= TARGET_PER_DAY else "⚠️"
    print("=" * 70)
    print("📊 THROUGHPUT MONITORING")
    print("=" * 70)
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"{hour_status} Last Hour: {posts_per_hour_actual}/{TARGET_PER_HOUR} posts")
    print(f"{day_status} Last 24h: {posts_per_day_actual}/{TARGET_PER_DAY} posts")
    print(f"📈 Today: {posts_today_count} posts")
    print()
    # Projection
    hours_elapsed = now.hour + (now.minute / 60)
    if hours_elapsed > 0:
        projected_daily = int((posts_today_count / hours_elapsed) * 24)
        proj_status = "✅" if projected_daily >= TARGET_PER_DAY else "⚠️"
        print(f"{proj_status} Projected Daily: {projected_daily} posts")
    print("=" * 70)
    # Queue status
    stories_ready = supabase.table("stories").select(
        "id"
    ).eq("is_validated", True).eq("posted", False).execute().data
    print(f"📚 Queue: {len(stories_ready)} stories ready to post")
    print("=" * 70)

if __name__ == "__main__":
    check_throughput()
