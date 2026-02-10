"""Preview posts WITHOUT publishing to Instagram"""
import asyncio
import sys
sys.path.insert(0, 'D:\\FNO_HOUSE\\my_project\\fastnewsorg')

from scheduler import fetch_rss_articles, get_content_editor, validate_article
from quality_filter.content_processor import (
    relaxed_quality_filter, 
    detect_content_category,
    generate_smart_caption,
    get_category_emoji
)

async def preview_posts(count=5):
    """Show what would be posted WITHOUT actually posting"""
    
    print("\n" + "="*70)
    print("📋 POST PREVIEW (DRY RUN - NOT POSTING TO INSTAGRAM)")
    print("="*70 + "\n")
    
    # Fetch articles
    articles = await fetch_rss_articles(limit=25)
    
    if not articles:
        print("❌ No articles found in database")
        return
    
    print(f"Found {len(articles)} articles in database\n")
    
    previews = []
    
    for article in articles:
        if len(previews) >= count:
            break
            
        # Quality filter
        if not relaxed_quality_filter(article):
            continue
        
        # AI validation
        should_publish, category, metadata = validate_article(
            title=article['title'],
            summary=article['summary'],
            source=article['source'],
            content=article.get('content', '')
        )
        
        if not should_publish:
            continue
        
        # Generate caption
        emoji = get_category_emoji(category)
        caption = generate_smart_caption(
            article['title'],
            article['summary'],
            article['source']
        )
        full_caption = f"{emoji} {caption}"
        
        previews.append({
            'title': article['title'],
            'category': category,
            'emoji': emoji,
            'score': metadata.get('score', 0),
            'caption': full_caption,
            'has_image': bool(article.get('image'))
        })
    
    # Display previews
    print(f"✅ Found {len(previews)} posts ready to publish:\n")
    
    for i, post in enumerate(previews, 1):
        print("─" * 70)
        print(f"POST #{i}")
        print("─" * 70)
        print(f"Title: {post['title'][:80]}...")
        print(f"Category: {post['emoji']} {post['category'].upper()}")
        print(f"AI Score: {post['score']}/100")
        print(f"Has Image: {'✅' if post['has_image'] else '❌ (will use placeholder)'}")
        print(f"\nCaption Preview:")
        print("┌" + "─" * 68 + "┐")
        for line in post['caption'][:200].split('\n'):
            print(f"│ {line[:66]:<66} │")
        if len(post['caption']) > 200:
            print("│ ... (caption truncated)                                            │")
        print("└" + "─" * 68 + "┘")
        print()
    
    print("="*70)
    print(f"📊 SUMMARY: {len(previews)} posts ready")
    print("="*70)
    print("\n⚠️  This is a PREVIEW only - nothing posted to Instagram")
    print("\nTo actually post, run:")
    print("  python direct_post_test.py")
    print()

if __name__ == "__main__":
    asyncio.run(preview_posts())
