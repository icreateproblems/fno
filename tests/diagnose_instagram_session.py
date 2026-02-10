"""
Diagnostic script to check Instagram session and identify posting issues.
Run this to understand why posts aren't being made.
"""
import os
import sys
import json
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logger import get_logger
from app.config import INSTAGRAM_SESSION_FILE, SUPABASE_URL, SUPABASE_KEY
from app.db_pool import get_supabase_client

logger = get_logger(__name__)

def check_session_file():
    """Check if Instagram session file exists and is valid"""
    print("\n" + "="*70)
    print("1️⃣  CHECKING INSTAGRAM SESSION FILE")
    print("="*70)
    
    if not os.path.exists(INSTAGRAM_SESSION_FILE):
        print(f"❌ Session file NOT found: {INSTAGRAM_SESSION_FILE}")
        print("   Fix: Run 'python scripts/ig_login.py' to create session")
        return False
    
    print(f"✅ Session file exists: {INSTAGRAM_SESSION_FILE}")
    
    # Check file size
    file_size = os.path.getsize(INSTAGRAM_SESSION_FILE)
    print(f"   File size: {file_size} bytes")
    
    if file_size < 100:
        print("❌ Session file is too small (likely corrupted)")
        return False
    
    # Try to parse JSON
    try:
        with open(INSTAGRAM_SESSION_FILE, 'r') as f:
            session_data = json.load(f)
        print(f"✅ Session file is valid JSON")
        print(f"   Keys in session: {len(session_data)}")
        
        # Check for critical fields
        critical_fields = ['sessionid', 'csrf_token', 'userid']
        missing = []
        for field in critical_fields:
            if field in session_data:
                print(f"   ✅ {field}: Present")
            else:
                print(f"   ❌ {field}: MISSING")
                missing.append(field)
        
        if missing:
            print(f"\n⚠️  Session is missing critical fields: {missing}")
            print("   Fix: Run 'python scripts/ig_login.py' to regenerate")
            return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Session file is NOT valid JSON: {e}")
        print("   Fix: Run 'python scripts/ig_login.py' to regenerate")
        return False
    except Exception as e:
        print(f"❌ Error reading session file: {e}")
        return False


def check_database():
    """Check database and story counts"""
    print("\n" + "="*70)
    print("2️⃣  CHECKING DATABASE")
    print("="*70)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL or SUPABASE_KEY not configured")
        return False
    
    try:
        supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check stories
        stories_response = supabase.table("stories").select("*").execute()
        total_stories = len(stories_response.data)
        print(f"✅ Database connection OK")
        print(f"   Total stories in DB: {total_stories}")
        
        if total_stories == 0:
            print("   ⚠️  No stories found! Run: python scripts/fetch_news.py")
            return False
        
        # Count validated stories
        validated = [s for s in stories_response.data if s.get('is_validated')]
        print(f"   Validated stories: {len(validated)}")
        
        # Count unposted stories
        unposted = [s for s in stories_response.data if not s.get('posted')]
        print(f"   Unposted stories: {len(unposted)}")
        
        # Count both
        unposted_validated = [s for s in stories_response.data if s.get('is_validated') and not s.get('posted')]
        print(f"   Unposted & Validated: {len(unposted_validated)}")
        
        if len(unposted_validated) == 0:
            print("   ⚠️  No unposted validated stories! These have been posted or rejected.")
            if len(unposted) > 0:
                print(f"   💡 You have {len(unposted)} unvalidated stories that could be processed")
        
        # Check posting history
        history_response = supabase.table("posting_history").select("*").execute()
        total_posts = len(history_response.data)
        successful_posts = len([h for h in history_response.data if h.get('success')])
        
        print(f"   Total post attempts: {total_posts}")
        print(f"   Successful posts: {successful_posts}")
        
        # Check today's posts
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_posts = supabase.table("posting_history").select("*").gte("created_at", today).execute().data
        today_successful = len([h for h in today_posts if h.get('success')])
        
        print(f"   Posts today: {len(today_posts)} ({today_successful} successful)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_posting_logic():
    """Check if posting logic would allow a post"""
    print("\n" + "="*70)
    print("3️⃣  CHECKING POSTING LOGIC")
    print("="*70)
    
    # Import the posting module
    from scripts.post_instagram import should_post_now, check_daily_limit
    from datetime import datetime, timedelta, timezone
    
    # Nepal timezone (UTC+5:45)
    NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))
    
    # Check random posting decision
    print("Random posting check (should_post_now):")
    nepal_time = datetime.now(NEPAL_TZ)
    print(f"   Current Nepal time: {nepal_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Hour: {nepal_time.hour}")
    
    current_hour = nepal_time.hour
    if 1 <= current_hour < 6:
        print(f"   ⚠️  In sleeping hours (1-6am) - posting disabled")
    else:
        print(f"   ✅ Not in sleeping hours - OK to post")
        
    # Check daily limit
    print("\nDaily limit check:")
    try:
        supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
        daily_ok = check_daily_limit(supabase)
        if daily_ok:
            print(f"   ✅ Daily limit OK")
        else:
            print(f"   ❌ Daily limit reached (20 posts/day)")
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")


def check_credentials():
    """Check if all required credentials are set"""
    print("\n" + "="*70)
    print("4️⃣  CHECKING ENVIRONMENT VARIABLES")
    print("="*70)
    
    required = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
    }
    
    all_ok = True
    for key, value in required.items():
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ❌ {key}: NOT SET")
            all_ok = False
    
    return all_ok


def main():
    print("\n" + "="*70)
    print("🔍 INSTAGRAM BOT DIAGNOSTIC REPORT")
    print("="*70)
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    session_ok = check_session_file()
    db_ok = check_database()
    creds_ok = check_credentials()
    check_posting_logic()
    
    # Summary
    print("\n" + "="*70)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("="*70)
    
    if not session_ok:
        print("⚠️  SESSION ISSUE DETECTED:")
        print("   1. Run: python scripts/ig_login.py")
        print("   2. Enter your Instagram username & password")
        print("   3. A new ig_session.json will be created")
        print("   4. Try posting again")
    else:
        print("✅ Session looks OK")
    
    if not db_ok:
        print("\n⚠️  DATABASE ISSUE:")
        print("   1. Check SUPABASE_URL and SUPABASE_KEY are correct")
        print("   2. Run: python scripts/fetch_news.py")
        print("   3. This will fetch news stories into the database")
    else:
        print("\n✅ Database connection OK")
    
    if not creds_ok:
        print("\n⚠️  CREDENTIALS MISSING:")
        print("   Make sure .env file has all required variables")
    else:
        print("\n✅ All credentials set")
    
    print("\n" + "="*70)
    print("QUICK FIXES:")
    print("="*70)
    print("1️⃣  Fetch news: python scripts/fetch_news.py")
    print("2️⃣  Create session: python scripts/ig_login.py")
    print("3️⃣  Test manual post: python test_manual_post.py")
    print("4️⃣  Check logs: tail -f logs/news_bot.log")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
