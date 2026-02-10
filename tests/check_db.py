"""Quick database check"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db_pool import get_supabase_client
from app.config import Config

print("Checking database tables...")

supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Try stories table with all columns
try:
    result = supabase.table('stories').select('*').limit(5).execute()
    print(f"\n✅ 'stories' table exists with {len(result.data)} sample records")
    
    if result.data:
        print("\nAvailable columns:")
        if result.data:
            print(f"   {list(result.data[0].keys())}")
        
        print("\nSample stories:")
        for i, story in enumerate(result.data, 1):
            headline = story.get('headline', story.get('title', 'No title'))
            print(f"{i}. {headline[:60]}...")
            print(f"   Posted: {story.get('posted', False)}")
            print(f"   Columns: {list(story.keys())[:10]}")
    else:
        print("⚠️  No stories in database yet - run scripts/fetch_news.py")
        
except Exception as e:
    print(f"❌ 'stories' table error: {e}")

# Try raw_stories table
try:
    result = supabase.table('raw_stories').select('*').limit(1).execute()
    print(f"\n✅ 'raw_stories' table exists")
except Exception as e:
    print(f"\n❌ 'raw_stories' table does not exist: {e}")
