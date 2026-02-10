"""
Quick test script to check what's preventing posts.
Runs the full posting pipeline with FORCE_POST=true.
"""
import os
import sys
import subprocess

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"📋 {title}")
    print("="*70)

def run_command(cmd, description):
    """Run a command and show output"""
    print(f"\n▶️  {description}")
    print(f"   Command: {cmd}\n")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    print_section("INSTAGRAM BOT - QUICK TEST")
    
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    
    # Step 1: Check Python environment
    print_section("STEP 1: Check Environment")
    ok = run_command("python --version", "Check Python version")
    if not ok:
        print("❌ Python not found!")
        return
    
    # Step 2: Check if session file exists
    print_section("STEP 2: Check Session File")
    if os.path.exists("ig_session.json"):
        print("✅ ig_session.json found")
        size = os.path.getsize("ig_session.json")
        print(f"   Size: {size} bytes")
        if size < 100:
            print("⚠️  File is very small - might be corrupted")
            print("   Run: python scripts/ig_login.py")
    else:
        print("❌ ig_session.json NOT found!")
        print("   Run: python scripts/ig_login.py")
        return
    
    # Step 3: Fetch fresh news
    print_section("STEP 3: Fetch Fresh News")
    ok = run_command("python scripts/fetch_news.py", "Fetching news stories...")
    if not ok:
        print("❌ News fetch failed - check logs/news_bot.log")
    
    # Step 4: Test post with FORCE_POST
    print_section("STEP 4: Test Manual Post")
    print("Running test with FORCE_POST=true (bypasses random checks)...")
    run_command("python test_manual_post.py", "Testing Instagram post...")
    
    # Step 5: Check logs
    print_section("STEP 5: Check Results")
    print("✅ Test complete! Check the results above.")
    print("\nFor detailed logs, check: logs/news_bot.log")
    print("\nFor diagnostics, run: python diagnose_instagram_session.py")

if __name__ == "__main__":
    main()
