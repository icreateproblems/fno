"""Direct test of posting function"""
import asyncio
import sys
sys.path.insert(0, 'D:\\FNO_HOUSE\\my_project\\fastnewsorg')

from scheduler import hourly_publish_burst

async def main():
    print("\n" + "="*70)
    print("⚠️  WARNING: THIS WILL POST TO YOUR LIVE INSTAGRAM ACCOUNT!")
    print("="*70)
    print("\nThis is NOT a dry run - posts will be published immediately.")
    print("\nTo preview posts WITHOUT publishing, run:")
    print("  python preview_posts.py")
    print("\n" + "="*70)
    
    confirm = input("\nType 'YES' to continue with LIVE posting: ").strip()
    
    if confirm != "YES":
        print("\n❌ Cancelled. No posts published.")
        return
    
    print("\n🚀 Testing Instagram posting directly...")
    print("-" * 70)
    result = await hourly_publish_burst()
    print("-" * 70)
    print(f"✅ Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
