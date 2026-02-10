"""Test posting ONE article with placeholder image to verify it works"""
import asyncio
import sys
sys.path.insert(0, 'D:\\FNO_HOUSE\\my_project\\fastnewsorg')

from scheduler import (
    fetch_rss_articles, 
    validate_article,
    publish_instagram_graph,
    get_content_editor
)
from quality_filter.content_processor import (
    relaxed_quality_filter,
    detect_content_category,
    generate_smart_caption,
    get_category_emoji
)
from app.logger import get_logger

logger = get_logger(__name__)

async def test_single_post():
    """Post exactly ONE article to test image functionality"""
    
    print("\n" + "="*70)
    print("🧪 SINGLE POST TEST - IMAGE VERIFICATION")
    print("="*70 + "\n")
    
    # Fetch articles
    articles = await fetch_rss_articles(limit=10)
    
    if not articles:
        print("❌ No articles found")
        return
    
    # Find first valid article
    for article in articles:
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
        
        # Found a valid article!
        emoji = get_category_emoji(category)
        caption = generate_smart_caption(
            article['title'],
            article['summary'],
            article['source']
        )
        full_caption = f"{emoji} {caption}"
        
        print("Found article to post:")
        print(f"  Title: {article['title'][:60]}...")
        print(f"  Category: {emoji} {category}")
        print(f"  Score: {metadata.get('score')}/100")
        print(f"  Has Image: {'Yes' if article.get('image') else 'No (will use placeholder)'}")
        print(f"\nCaption preview:")
        print("  " + full_caption[:150] + "...")
        print()
        
        confirm = input("Post this to Instagram? Type 'YES' to confirm: ").strip().upper()
        
        if confirm != "YES":
            print("\n❌ Cancelled")
            return
        
        print("\n📤 Posting to Instagram...")
        
        success = await publish_instagram_graph(
            caption=full_caption,
            story_id=article.get('id'),
            category=category,
            article=article
        )
        
        if success:
            print("\n✅ SUCCESS! Post published to Instagram")
            print("   Go check your Instagram to see the post with image")
            print()
        else:
            print("\n❌ FAILED to post")
        
        return
    
    print("❌ No valid articles found to post")

if __name__ == "__main__":
    asyncio.run(test_single_post())
