"""Save posts to pending folder for review before publishing"""
import asyncio
import json
import os
from datetime import datetime
import sys
sys.path.insert(0, 'D:\\FNO_HOUSE\\my_project\\fastnewsorg')

from scheduler import (
    fetch_rss_articles, 
    validate_article
)
from quality_filter.content_processor import (
    relaxed_quality_filter,
    generate_smart_caption,
    get_category_emoji
)

PENDING_DIR = "pending_posts"

async def save_pending_posts(count=5):
    """Save posts to pending folder for review"""
    
    print("\n" + "="*70)
    print("💾 SAVING POSTS TO PENDING FOLDER")
    print("="*70 + "\n")
    
    # Create pending directory if not exists
    os.makedirs(PENDING_DIR, exist_ok=True)
    
    # Fetch articles
    articles = await fetch_rss_articles(limit=25)
    
    if not articles:
        print("❌ No articles found")
        return
    
    saved_count = 0
    
    for article in articles:
        if saved_count >= count:
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
        
        # Create post data
        post_data = {
            'id': article.get('id'),
            'title': article['title'],
            'summary': article['summary'],
            'source': article['source'],
            'category': category,
            'emoji': emoji,
            'ai_score': metadata.get('score', 0),
            'caption': full_caption,
            'image_url': article.get('image'),
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Save to JSON file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"post_{timestamp}_{saved_count + 1}.json"
        filepath = os.path.join(PENDING_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        saved_count += 1
        
        print(f"✅ Saved post #{saved_count}: {article['title'][:50]}...")
        print(f"   File: {filename}")
        print(f"   Category: {emoji} {category}")
        print(f"   Score: {metadata.get('score')}/100")
        print()
    
    print("="*70)
    print(f"✅ Saved {saved_count} posts to '{PENDING_DIR}' folder")
    print("="*70)
    print("\nNext steps:")
    print(f"  1. Review posts in '{PENDING_DIR}' folder")
    print("  2. Run: python review_pending_posts.py")
    print("  3. Approve and publish the ones you like")
    print()

if __name__ == "__main__":
    asyncio.run(save_pending_posts())
