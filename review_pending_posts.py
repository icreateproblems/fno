"""Review pending posts and publish selected ones"""
import asyncio
import json
import os
import sys
sys.path.insert(0, 'D:\\FNO_HOUSE\\my_project\\fastnewsorg')

from scheduler import publish_instagram_graph

PENDING_DIR = "pending_posts"

def list_pending_posts():
    """List all pending posts"""
    
    if not os.path.exists(PENDING_DIR):
        print(f"❌ No pending posts folder found")
        return []
    
    posts = []
    for filename in sorted(os.listdir(PENDING_DIR)):
        if filename.endswith('.json'):
            filepath = os.path.join(PENDING_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                post_data = json.load(f)
                post_data['filename'] = filename
                posts.append(post_data)
    
    return posts

def display_post(post, index):
    """Display a single post for review"""
    print("\n" + "─"*70)
    print(f"POST #{index}")
    print("─"*70)
    print(f"File: {post['filename']}")
    print(f"Title: {post['title'][:70]}...")
    print(f"Category: {post['emoji']} {post['category'].upper()}")
    print(f"AI Score: {post['ai_score']}/100")
    print(f"Has Image: {'✅' if post.get('image_url') else '❌ (will use placeholder)'}")
    print(f"\n📝 CAPTION:")
    print("┌" + "─"*68 + "┐")
    for line in post['caption'][:300].split('\n'):
        print(f"│ {line[:66]:<66} │")
    if len(post['caption']) > 300:
        print("│ ... (caption continues)                                             │")
    print("└" + "─"*68 + "┘")

async def publish_post(post):
    """Publish a single post to Instagram"""
    
    print(f"\n📤 Publishing to Instagram...")
    
    success = await publish_instagram_graph(
        caption=post['caption'],
        story_id=post.get('id'),
        category=post['category'],
        title=post['title'],
        summary=post.get('summary', ''),
        source=post.get('source', 'FastNews.org')
    )
    
    if success:
        # Mark as published - delete the file
        filepath = os.path.join(PENDING_DIR, post['filename'])
        os.remove(filepath)
        print(f"✅ Published and removed from pending")
        return True
    else:
        print(f"❌ Failed to publish")
        return False

async def review_and_publish():
    """Interactive review and publish interface"""
    
    print("\n" + "="*70)
    print("📋 REVIEW PENDING POSTS")
    print("="*70)
    
    posts = list_pending_posts()
    
    if not posts:
        print("\n❌ No pending posts found")
        print(f"\nRun this first: python save_pending_posts.py")
        return
    
    print(f"\nFound {len(posts)} pending posts\n")
    
    for i, post in enumerate(posts, 1):
        display_post(post, i)
        
        print("\nOptions:")
        print("  [P] Publish this post to Instagram")
        print("  [S] Skip to next post")
        print("  [D] Delete this post (won't publish)")
        print("  [Q] Quit review")
        
        choice = input("\nYour choice (P/S/D/Q): ").strip().upper()
        
        if choice == 'P':
            published = await publish_post(post)
            if published:
                print(f"\n🎉 Post #{i} is now LIVE on Instagram!")
                input("\nPress Enter to continue...")
        
        elif choice == 'D':
            filepath = os.path.join(PENDING_DIR, post['filename'])
            os.remove(filepath)
            print(f"\n🗑️  Deleted post #{i}")
            input("\nPress Enter to continue...")
        
        elif choice == 'Q':
            print("\n👋 Exiting review...")
            break
        
        else:
            print(f"\n⏭️  Skipped post #{i}")
    
    # Show remaining
    remaining = list_pending_posts()
    print("\n" + "="*70)
    print(f"📊 SUMMARY: {len(remaining)} posts still pending")
    print("="*70)
    if remaining:
        print(f"\nRun this again to review remaining posts:")
        print(f"  python review_pending_posts.py")
    print()

if __name__ == "__main__":
    asyncio.run(review_and_publish())
