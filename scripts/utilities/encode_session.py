"""
Utility script to encode ig_session.json to base64 for CircleCI.
Use this after running ig_login.py to get the encoded session.
"""
import base64
import os
import sys

def main():
    session_file = "ig_session.json"
    
    if not os.path.exists(session_file):
        print(f"❌ Error: {session_file} not found!")
        print("   Run 'python scripts/ig_login.py' first to create the session.")
        sys.exit(1)
    
    print("=" * 70)
    print("📦 ENCODING INSTAGRAM SESSION FOR CIRCLECI")
    print("=" * 70)
    
    with open(session_file, "r") as f:
        session_data = f.read()
    
    # Validate it's JSON
    try:
        import json
        json.loads(session_data)
        print("✅ Session file is valid JSON")
    except json.JSONDecodeError:
        print("❌ Warning: Session file doesn't look like valid JSON")
    
    # Encode to base64
    encoded = base64.b64encode(session_data.encode()).decode()
    
    print(f"\n✅ Encoded {len(session_data)} bytes → {len(encoded)} characters")
    print("\n" + "=" * 70)
    print("📋 BASE64 ENCODED SESSION (Copy this to CircleCI):")
    print("=" * 70)
    print(encoded)
    print("\n" + "=" * 70)
    print("\n🚀 NEXT STEPS:")
    print("   1. Copy the base64 string above")
    print("   2. Go to CircleCI project settings")
    print("   3. Update environment variable: IG_SESSION_JSON")
    print("   4. Paste the base64 string")
    print("=" * 70)

if __name__ == "__main__":
    main()
