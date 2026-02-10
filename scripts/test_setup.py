import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "GROQ_API_KEY",
]

def main():
    ok = True
    for k in REQUIRED:
        if not os.getenv(k):
            print("❌ Missing", k)
            ok = False
        else:
            print("✅", k)

    if not os.path.exists("ig_session.json"):
        print("❌ Missing ig_session.json (run scripts/ig_login.py)")
        ok = False
    else:
        print("✅ ig_session.json")

    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
