#!/usr/bin/env python3
"""
System Health Check - Verify News_Bot is production-ready
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import *
from app.logger import get_logger
from app.db import init_database
from app.db_pool import get_supabase_client
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)


def check_environment():
    """Check all environment variables"""
    print("\n" + "=" * 60)
    print("ENVIRONMENT CHECK")
    print("=" * 60)
    
    required = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "GROQ_API_KEY": GROQ_API_KEY,
        "IG_USERNAME": os.getenv("IG_USERNAME"),
        "IG_PASSWORD": os.getenv("IG_PASSWORD")
    }
    
    all_ok = True
    for key, value in required.items():
        if value and len(str(value)) > 10:
            print(f"✅ {key}: {str(value)[:20]}...")
        else:
            print(f"❌ {key}: MISSING or INVALID")
            all_ok = False
    
    return all_ok


def check_database():
    """Check database connectivity"""
    print("\n" + "=" * 60)
    print("DATABASE CHECK")
    print("=" * 60)
    
    try:
        if not init_database(SUPABASE_URL, SUPABASE_KEY):
            print("❌ Database initialization failed")
            return False
        
        print("✅ Database connection successful")
        
        supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check tables
        stories = supabase.table("stories").select("id").limit(1).execute()
        print(f"✅ Stories table accessible ({len(stories.data)} records)")
        
        history = supabase.table("posting_history").select("id").limit(1).execute()
        print(f"✅ Posting history table accessible ({len(history.data)} records)")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_files():
    """Check critical files exist"""
    print("\n" + "=" * 60)
    print("FILES CHECK")
    print("=" * 60)
    
    files = {
        "Template": TEMPLATE_PATH,
        "Session": INSTAGRAM_SESSION_FILE,
        "Title Font": TITLE_FONT_PATH,
        "Body Font": BODY_FONT_PATH
    }
    
    all_ok = True
    for name, path in files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ {name}: {path} ({size} bytes)")
        else:
            print(f"❌ {name}: {path} NOT FOUND")
            all_ok = False
    
    return all_ok


def check_posting_rate():
    """Check recent posting activity"""
    print("\n" + "=" * 60)
    print("POSTING ACTIVITY CHECK")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Last 24 hours
        now = datetime.now()
        yesterday = now.replace(hour=now.hour - 24).isoformat()
        
        posts = (
            supabase.table("posting_history")
            .select("*")
            .gte("created_at", yesterday)
            .execute()
            .data
        )
        
        successful = [p for p in posts if p.get("success")]
        failed = [p for p in posts if not p.get("success")]
        
        print(f"✅ Posts in last 24h: {len(posts)}")
        print(f"   - Successful: {len(successful)}")
        print(f"   - Failed: {len(failed)}")
        
        if failed:
            print("\nRecent failures:")
            for f in failed[-3:]:
                print(f"   - {f.get('error_message', 'Unknown')[:60]}")
        
        # Check validated stories ready to post
        ready = (
            supabase.table("stories")
            .select("id")
            .eq("is_validated", True)
            .eq("posted", False)
            .execute()
            .data
        )
        
        print(f"✅ Validated stories ready: {len(ready)}")
        
        return True
    except Exception as e:
        print(f"❌ Could not check posting activity: {e}")
        return False


def main():
    """Run all health checks"""
    print("\n" + "=" * 60)
    print("NEWS_BOT SYSTEM HEALTH CHECK")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    checks = {
        "Environment": check_environment(),
        "Database": check_database(),
        "Files": check_files(),
        "Posting Activity": check_posting_rate()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, status in checks.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {name}: {'PASS' if status else 'FAIL'}")
    
    all_pass = all(checks.values())
    
    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 ALL CHECKS PASSED - SYSTEM READY FOR PRODUCTION")
    else:
        print("⚠️  SOME CHECKS FAILED - REVIEW ERRORS ABOVE")
    print("=" * 60 + "\n")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
