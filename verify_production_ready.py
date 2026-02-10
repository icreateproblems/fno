"""
Production Readiness Verification Script
Run this before deploying to ensure all systems are ready.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_env_variables():
    """Verify all required environment variables are set"""
    print("\n" + "=" * 70)
    print("🔍 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 70)
    
    required_vars = {
        'SUPABASE_URL': 'Database connection',
        'SUPABASE_KEY': 'Database authentication',
        'GROQ_API_KEY': 'AI caption generation',
        'IG_USERNAME': 'Instagram account',
        'IG_PASSWORD': 'Instagram password',
        'TELEGRAM_BOT_TOKEN': 'Alert notifications',
        'TELEGRAM_CHAT_ID': 'Alert destination'
    }
    
    all_good = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var:20} = {masked:20} ({description})")
        else:
            print(f"❌ {var:20} = NOT SET ({description})")
            all_good = False
    
    return all_good


def check_instagram_session():
    """Verify Instagram session file exists and is valid"""
    print("\n" + "=" * 70)
    print("🔍 CHECKING INSTAGRAM SESSION")
    print("=" * 70)
    
    session_file = "ig_session.json"
    
    if not os.path.exists(session_file):
        print(f"❌ Session file not found: {session_file}")
        print("   Run: python fix_instagram_session.py")
        return False
    
    print(f"✅ Session file exists: {session_file}")
    
    # Check if valid JSON
    try:
        with open(session_file, 'r') as f:
            data = json.load(f)
        print("✅ Session file is valid JSON")
        
        # Check for required keys
        required_keys = ['authorization_data', 'device_settings', 'cookies']
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f"⚠️  Warning: Missing keys in session: {missing}")
        else:
            print("✅ Session has all required keys")
        
        # Check session age
        import time
        file_age_days = (time.time() - os.path.getmtime(session_file)) / 86400
        print(f"📅 Session age: {file_age_days:.1f} days")
        
        if file_age_days > 25:
            print("⚠️  Warning: Session is old (>25 days). Consider regenerating soon.")
        elif file_age_days > 30:
            print("❌ Session is expired (>30 days). Regenerate now!")
            return False
        else:
            print("✅ Session is fresh")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Session file is corrupted: {e}")
        print("   Run: python fix_instagram_session.py")
        return False
    except Exception as e:
        print(f"❌ Error reading session: {e}")
        return False


def check_required_files():
    """Verify all required files exist"""
    print("\n" + "=" * 70)
    print("🔍 CHECKING REQUIRED FILES")
    print("=" * 70)
    
    required_files = {
        'scripts/fetch_news.py': 'News fetching script',
        'scripts/post_instagram.py': 'Instagram posting script',
        'scripts/template_render.py': 'Template renderer',
        'scripts/groq_caption.py': 'Caption generator',
        'templates/instagram_template_improved.jpg': 'Instagram template',
        'app/config.py': 'Configuration',
        'app/db.py': 'Database module',
        'app/logger.py': 'Logger module',
        'requirements.txt': 'Dependencies'
    }
    
    all_good = True
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"✅ {file_path:45} ({description})")
        else:
            print(f"❌ {file_path:45} MISSING ({description})")
            all_good = False
    
    return all_good


def check_circleci_config():
    """Verify CircleCI configuration"""
    print("\n" + "=" * 70)
    print("🔍 CHECKING CIRCLECI CONFIGURATION")
    print("=" * 70)
    
    config_file = ".circleci/config.yml"
    
    if not os.path.exists(config_file):
        print(f"❌ CircleCI config not found: {config_file}")
        return False
    
    print(f"✅ CircleCI config exists: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key configurations
    checks = [
        ('IG_SESSION_JSON', 'Instagram session variable'),
        ('SUPABASE_URL', 'Database URL variable'),
        ('GROQ_API_KEY', 'AI API key variable'),
        ('scheduled-fetch', 'Scheduled workflow'),
        ('fetch-and-post', 'Main job')
    ]
    
    for check_str, description in checks:
        if check_str in content:
            print(f"✅ Found: {check_str:30} ({description})")
        else:
            print(f"⚠️  Missing: {check_str:30} ({description})")
    
    return True


def test_database_connection():
    """Test connection to Supabase"""
    print("\n" + "=" * 70)
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 70)
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
            return False
        
        supabase = create_client(url, key)
        
        # Try a simple query on the correct table name
        result = supabase.table('stories').select('id').limit(1).execute()
        
        print("✅ Database connection successful")
        print(f"✅ Can access stories table")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_groq_api():
    """Test Groq API for caption generation"""
    print("\n" + "=" * 70)
    print("🔍 TESTING GROQ API")
    print("=" * 70)
    
    try:
        from groq import Groq
        
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            print("❌ Missing GROQ_API_KEY")
            return False
        
        client = Groq(api_key=api_key)
        
        # Try a simple completion
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )
        
        print("✅ Groq API connection successful")
        print(f"✅ Model response received")
        return True
        
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
        return False


def main():
    """Run all checks"""
    print("\n" + "=" * 70)
    print("🚀 PRODUCTION READINESS VERIFICATION")
    print("=" * 70)
    
    results = {
        'Environment Variables': check_env_variables(),
        'Instagram Session': check_instagram_session(),
        'Required Files': check_required_files(),
        'CircleCI Config': check_circleci_config(),
        'Database Connection': test_database_connection(),
        'Groq API': test_groq_api()
    }
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    for check, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check}")
    
    print("\n" + "=" * 70)
    
    if all(results.values()):
        print("✅ ALL CHECKS PASSED - PRODUCTION READY! 🎉")
        print("=" * 70)
        print("\n🚀 NEXT STEPS:")
        print("1. Commit and push to main branch")
        print("2. Update CircleCI environment variable: IG_SESSION_JSON")
        print("3. Trigger pipeline or wait for scheduled run")
        print("4. Monitor logs for successful posts")
        print("\n✅ Bot will post automatically every 30 minutes (with 60% random skip)")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - FIX ISSUES BEFORE DEPLOYING")
        print("=" * 70)
        failed = [k for k, v in results.items() if not v]
        print("\n⚠️  Failed checks:")
        for check in failed:
            print(f"   - {check}")
        print("\n🔧 Fix the issues above and run this script again.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
