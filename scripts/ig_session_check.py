"""
Check if Instagram session is still valid.
Run this before posting to avoid account lockouts.
"""
import os
import sys
from instagrapi import Client

def main():
    if not os.path.exists("ig_session.json"):
        print("❌ No session found. Run: python scripts/ig_login.py")
        sys.exit(1)
    
    print("🔍 Validating Instagram session...")
    try:
        cl = Client()
        cl.load_settings("ig_session.json")
        
        # Test session by getting user info (minimal API call)
        user = cl.account_info()
        print(f"✅ Session valid! Logged in as @{user.username}")
        print(f"   Account: {user.full_name}")
        print(f"   Followers: {user.follower_count:,}")
        return 0
    except Exception as e:
        print(f"❌ Session expired or invalid: {e}")
        print("\n💡 Fix: Run 'python scripts/ig_login.py' to create a new session")
        sys.exit(1)

if __name__ == "__main__":
    main()
