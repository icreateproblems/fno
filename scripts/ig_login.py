import getpass
import os
import sys
from instagrapi import Client

def main():
    # Safety check: warn if session already exists
    if os.path.exists("ig_session.json"):
        print("⚠️  ig_session.json already exists!")
        response = input("Overwrite existing session? (type 'yes' to confirm): ").strip().lower()
        if response != "yes":
            print("❌ Cancelled. Keeping existing session.")
            return
        print("\n🔄 Creating new session...")
    
    # Require explicit confirmation to prevent accidental runs
    print("\n⚠️  WARNING: This will log in to Instagram with your credentials.")
    print("   Your password will NOT be stored (only session token).")
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Cancelled.")
        return

    username = input("\nInstagram username: ").strip()
    password = getpass.getpass("Instagram password: ").strip()

    if not username or not password:
        print("❌ Username and password are required.")
        return

    print("\n🔐 Attempting login...")
    try:
        cl = Client()
        cl.login(username, password)
        cl.dump_settings("ig_session.json")
        print("✅ Saved ig_session.json (DO NOT COMMIT THIS FILE).")
        print("   Session valid for ~1 month. Re-run this script if it expires.")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
