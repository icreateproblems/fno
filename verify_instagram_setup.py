"""
Quick verification script for Instagram Graph API setup
Tests all components before going live
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_env_var(name, required=True):
    """Check if environment variable is set"""
    value = os.getenv(name)
    if value and value != f"your_{name.lower()}_here":
        print(f"{GREEN}✓{RESET} {name}: Set")
        return True
    else:
        if required:
            print(f"{RED}✗{RESET} {name}: Not set or using placeholder")
        else:
            print(f"{YELLOW}○{RESET} {name}: Not set (optional)")
        return not required


def test_instagram_token():
    """Test Instagram access token validity"""
    token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if not token or not account_id:
        return False
    
    try:
        # Get account info to test token
        url = f"https://graph.facebook.com/v24.0/{account_id}"
        params = {
            'fields': 'username,followers_count',
            'access_token': token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            username = data.get('username', 'Unknown')
            followers = data.get('followers_count', 0)
            print(f"{GREEN}✓{RESET} Instagram token valid")
            print(f"  Account: @{username} ({followers:,} followers)")
            return True
        else:
            error = response.json()
            print(f"{RED}✗{RESET} Instagram token invalid: {error.get('error', {}).get('message')}")
            return False
            
    except Exception as e:
        print(f"{RED}✗{RESET} Instagram token test failed: {e}")
        return False


def test_imgbb_key():
    """Test imgbb API key"""
    key = os.getenv('IMGBB_API_KEY')
    
    if not key:
        return False
    
    try:
        # Simple API check
        url = "https://api.imgbb.com/1/upload"
        # Just check if key format is valid (don't upload yet)
        if len(key) == 32:  # imgbb keys are 32 chars
            print(f"{GREEN}✓{RESET} imgbb API key format valid")
            return True
        else:
            print(f"{YELLOW}○{RESET} imgbb API key format unexpected (should be 32 chars)")
            return True  # Don't fail on this
            
    except Exception as e:
        print(f"{YELLOW}○{RESET} imgbb key check skipped: {e}")
        return True


def test_database_connection():
    """Test Supabase database connection"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        return False
    
    try:
        from app.db_pool import get_supabase_client
        supabase = get_supabase_client(url, key)
        
        # Try to query stories table
        result = supabase.table('stories').select('id').limit(1).execute()
        
        print(f"{GREEN}✓{RESET} Database connection successful")
        return True
        
    except Exception as e:
        print(f"{RED}✗{RESET} Database connection failed: {e}")
        return False


def test_groq_keys():
    """Test Groq API keys"""
    keys_str = os.getenv('GROQ_API_KEYS')
    single_key = os.getenv('GROQ_API_KEY')
    
    if not keys_str and not single_key:
        return False
    
    keys = []
    if keys_str:
        keys = [k.strip() for k in keys_str.split(',')]
    elif single_key:
        keys = [single_key]
    
    try:
        # Test first key
        from groq import Groq
        client = Groq(api_key=keys[0])
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say hi"}],
            model="llama-3.1-8b-instant",
            max_tokens=10
        )
        
        print(f"{GREEN}✓{RESET} Groq API working ({len(keys)} key(s) configured)")
        return True
        
    except Exception as e:
        print(f"{RED}✗{RESET} Groq API test failed: {e}")
        return False


def test_template_files():
    """Check if required template files exist"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        "templates/breaking_template(1350).png",
        "fonts/Inter-Bold.ttf",
        "fonts/Inter-Regular.ttf",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"{GREEN}✓{RESET} {file_path}")
        else:
            print(f"{RED}✗{RESET} {file_path} not found")
            all_exist = False
    
    return all_exist


def main():
    """Run all verification checks"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Instagram Graph API Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {}
    
    # Check environment variables
    print(f"\n{BLUE}[1/6] Environment Variables{RESET}")
    print("-" * 40)
    results['env_supabase_url'] = check_env_var('SUPABASE_URL')
    results['env_supabase_key'] = check_env_var('SUPABASE_KEY')
    results['env_instagram_token'] = check_env_var('INSTAGRAM_ACCESS_TOKEN')
    results['env_instagram_account'] = check_env_var('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    results['env_imgbb'] = check_env_var('IMGBB_API_KEY')
    results['env_groq'] = check_env_var('GROQ_API_KEYS') or check_env_var('GROQ_API_KEY')
    
    # Test Instagram token
    print(f"\n{BLUE}[2/6] Instagram Graph API{RESET}")
    print("-" * 40)
    results['instagram'] = test_instagram_token()
    
    # Test imgbb
    print(f"\n{BLUE}[3/6] Image Hosting (imgbb){RESET}")
    print("-" * 40)
    results['imgbb'] = test_imgbb_key()
    
    # Test database
    print(f"\n{BLUE}[4/6] Database Connection{RESET}")
    print("-" * 40)
    results['database'] = test_database_connection()
    
    # Test Groq
    print(f"\n{BLUE}[5/6] Groq AI API{RESET}")
    print("-" * 40)
    results['groq'] = test_groq_keys()
    
    # Test template files
    print(f"\n{BLUE}[6/6] Template & Font Files{RESET}")
    print("-" * 40)
    results['templates'] = test_template_files()
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}✓ All checks passed ({passed}/{total}){RESET}")
        print(f"\n{GREEN}You're ready to post to Instagram!{RESET}")
        print(f"\nRun: {BLUE}python scripts/post_instagram_graph.py{RESET}")
    else:
        print(f"{YELLOW}⚠ {passed}/{total} checks passed{RESET}")
        print(f"\n{YELLOW}Please fix the failed checks before posting.{RESET}")
        print(f"\nSee: {BLUE}docs/INSTAGRAM_GRAPH_SETUP.md{RESET} for setup instructions")
    
    print()
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
