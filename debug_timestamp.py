from app.db_pool import get_supabase_client
from app.config import Config
from datetime import datetime
import pytz

# Get a story from database
supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
response = supabase.table('stories').select('*').limit(1).execute()

if response.data:
    story = response.data[0]
    print(f"Story created_at: {story.get('created_at')}")
    print(f"Type: {type(story.get('created_at'))}")
    
    # Try parsing
    created_at_str = story['created_at']
    print(f"\nParsing: {created_at_str}")
    
    # Try different parsing methods
    try:
        # Method 1: Replace Z with +00:00
        dt1 = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        print(f"✅ Method 1 (replace Z): {dt1}")
        print(f"   Timezone aware: {dt1.tzinfo is not None}")
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    try:
        # Method 2: Direct parsing
        dt2 = datetime.fromisoformat(created_at_str)
        print(f"✅ Method 2 (direct): {dt2}")
        print(f"   Timezone aware: {dt2.tzinfo is not None}")
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Test datetime.now()
    now_naive = datetime.now()
    now_aware = datetime.now(pytz.UTC)
    print(f"\ndatetime.now(): {now_naive}")
    print(f"  Timezone aware: {now_naive.tzinfo is not None}")
    print(f"\ndatetime.now(pytz.UTC): {now_aware}")
    print(f"  Timezone aware: {now_aware.tzinfo is not None}")
