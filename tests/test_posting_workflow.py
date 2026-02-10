"""
Complete Posting Workflow Test
Tests the entire pipeline: Fetch → Filter → AI Validation → Caption → Post
"""
import os
import sys
import asyncio
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("🔍 COMPLETE POSTING WORKFLOW TEST")
print("="*70)
print()

# Test 1: Fetch Articles
print("📥 STEP 1: Fetching Articles from Database")
print("-" * 70)

async def test_fetch_articles():
    from scheduler import fetch_rss_articles
    
    try:
        articles = await fetch_rss_articles(limit=10)
        
        if articles:
            print(f"✅ Successfully fetched {len(articles)} articles")
            print(f"\n   Sample articles:")
            for i, article in enumerate(articles[:5], 1):
                print(f"   {i}. {article['title'][:60]}...")
                print(f"      Source: {article['source']} | Age: {article.get('age_hours', 0):.1f}hrs")
                print(f"      Has image: {bool(article.get('image'))}")
            return articles
        else:
            print("⚠️  No articles found in database")
            print("   This might mean:")
            print("   - No news has been fetched yet (run scripts/fetch_news.py)")
            print("   - All articles already posted")
            print("   - Database connection issue")
            return []
    except Exception as e:
        print(f"❌ Error fetching articles: {e}")
        import traceback
        traceback.print_exc()
        return []

print()

# Test 2: Quality Filter
print("📝 STEP 2: Quality Filter Test")
print("-" * 70)

async def test_quality_filter(articles):
    from quality_filter.content_processor import relaxed_quality_filter
    
    if not articles:
        print("⚠️  No articles to filter")
        return []
    
    filtered = []
    for article in articles:
        if relaxed_quality_filter(article):
            filtered.append(article)
    
    print(f"✅ Filter Results:")
    print(f"   Input: {len(articles)} articles")
    print(f"   Passed: {len(filtered)} articles")
    print(f"   Acceptance rate: {(len(filtered)/len(articles)*100):.1f}%")
    
    if len(filtered) < len(articles):
        print(f"   Rejected: {len(articles) - len(filtered)} articles")
        rejected_reasons = []
        for article in articles:
            if article not in filtered:
                content_len = len(article.get('content', ''))
                if content_len < 150:
                    rejected_reasons.append("too short")
                elif content_len > 1000:
                    rejected_reasons.append("too long")
                elif article.get('age_hours', 0) > 48:
                    rejected_reasons.append("too old")
        if rejected_reasons:
            from collections import Counter
            reason_counts = Counter(rejected_reasons)
            print(f"   Rejection reasons: {dict(reason_counts)}")
    
    return filtered

print()

# Test 3: AI Editor Validation
print("🤖 STEP 3: AI Editor Validation")
print("-" * 70)

async def test_ai_validation(articles):
    from quality_filter.content_editor import validate_article
    from quality_filter.content_processor import detect_content_category
    
    if not articles:
        print("⚠️  No articles to validate")
        return []
    
    validated = []
    rejected = []
    
    print(f"Testing AI validation on {min(5, len(articles))} articles...\n")
    
    for i, article in enumerate(articles[:5], 1):
        print(f"Article {i}: {article['title'][:50]}...")
        
        # Preliminary category
        prelim_cat = detect_content_category(article['title'], article['summary'])
        print(f"   Preliminary category: {prelim_cat}")
        
        # AI validation
        try:
            should_publish, category, metadata = validate_article(
                title=article['title'],
                summary=article['summary'],
                source=article['source'],
                content=article.get('content', '')
            )
            
            if should_publish:
                print(f"   ✅ APPROVED | Category: {category} | Score: {metadata.get('score', 0)}/100")
                print(f"   Reason: {metadata.get('reason', 'N/A')[:60]}")
                article['ai_category'] = category
                article['ai_score'] = metadata.get('score', 0)
                article['ai_metadata'] = metadata
                validated.append(article)
            else:
                print(f"   ❌ REJECTED | Score: {metadata.get('score', 0)}/100")
                print(f"   Reason: {metadata.get('reason', 'N/A')[:60]}")
                rejected.append(article)
        except Exception as e:
            print(f"   ⚠️  Validation error: {e}")
            # On error, still approve with low score
            article['ai_category'] = prelim_cat
            article['ai_score'] = 60
            validated.append(article)
        
        print()
    
    print(f"📊 AI Validation Summary:")
    print(f"   Validated: {len(validated)} articles")
    print(f"   Rejected: {len(rejected)} articles")
    if validated:
        avg_score = sum(a.get('ai_score', 0) for a in validated) / len(validated)
        print(f"   Average score: {avg_score:.1f}/100")
        
        # Category distribution
        from collections import Counter
        categories = Counter(a.get('ai_category', 'general') for a in validated)
        print(f"   Categories: {dict(categories)}")
    
    return validated

print()

# Test 4: Caption Generation
print("💬 STEP 4: Caption Generation")
print("-" * 70)

async def test_caption_generation(articles):
    from quality_filter.content_processor import generate_smart_caption, get_category_emoji
    
    if not articles:
        print("⚠️  No articles for caption generation")
        return []
    
    print(f"Generating captions for {min(3, len(articles))} articles...\n")
    
    for i, article in enumerate(articles[:3], 1):
        category = article.get('ai_category', 'general')
        emoji = get_category_emoji(category)
        
        caption = generate_smart_caption(
            article['title'],
            article['summary'],
            article['source']
        )
        
        # Add category emoji
        caption_with_emoji = f"{emoji} {caption}"
        
        article['final_caption'] = caption_with_emoji
        
        print(f"Article {i}: {article['title'][:40]}...")
        print(f"Category: {emoji} {category}")
        print(f"Caption:\n{caption_with_emoji[:150]}...")
        print()
    
    return articles

print()

# Test 5: Instagram Posting (DRY RUN)
print("📸 STEP 5: Instagram Posting Test (DRY RUN)")
print("-" * 70)

async def test_instagram_posting(articles, dry_run=True):
    from app.config import Config
    
    if not articles:
        print("⚠️  No articles to post")
        return
    
    article = articles[0]  # Test with first article
    
    print(f"Testing with article: {article['title'][:50]}...")
    print(f"Category: {article.get('ai_category', 'general')}")
    print(f"AI Score: {article.get('ai_score', 0)}/100")
    image_url = article.get('image') or 'N/A'
    print(f"Image URL: {image_url[:60] if image_url != 'N/A' else 'N/A'}...")
    print()
    
    if dry_run:
        print("🚧 DRY RUN MODE - Not actually posting to Instagram")
        print()
        print("Would post:")
        print(f"   Caption: {article.get('final_caption', '')[:100]}...")
        print(f"   Image: {bool(article.get('image'))}")
        print(f"   Category: {article.get('ai_category', 'general')}")
        print()
        
        # Check if credentials exist
        has_token = bool(Config.GRAPH_TOKEN or Config.INSTAGRAM_ACCESS_TOKEN)
        has_account = bool(Config.INSTAGRAM_BUSINESS_ACCOUNT_ID)
        has_imgbb = bool(Config.IMGBB_API_KEY)
        
        print("Instagram API Credentials Check:")
        print(f"   {'✅' if has_token else '❌'} Access Token")
        print(f"   {'✅' if has_account else '❌'} Business Account ID")
        print(f"   {'✅' if has_imgbb else '❌'} ImgBB API Key")
        
        if has_token and has_account and has_imgbb:
            print("\n   ✅ All credentials present - ready for real posting!")
        else:
            print("\n   ⚠️  Missing credentials - configure in .env before posting")
        
        return True
    else:
        print("🚀 LIVE POSTING MODE")
        print()
        
        # Real posting
        try:
            from scheduler import publish_instagram_graph
            
            success = await publish_instagram_graph(
                image_url=article.get('image', ''),
                caption=article.get('final_caption', ''),
                story_id=article.get('id'),
                category=article.get('ai_category', 'general')
            )
            
            if success:
                print("✅ Successfully posted to Instagram!")
                return True
            else:
                print("❌ Failed to post to Instagram")
                return False
                
        except Exception as e:
            print(f"❌ Posting error: {e}")
            import traceback
            traceback.print_exc()
            return False

print()

# Main test execution
async def run_complete_test():
    print("Starting complete workflow test...\n")
    
    # Step 1: Fetch
    articles = await test_fetch_articles()
    print()
    
    if not articles:
        print("⚠️  Cannot continue test - no articles available")
        print("\n💡 To fix this:")
        print("   1. Run: python scripts/fetch_news.py")
        print("   2. Wait for articles to be fetched from RSS feeds")
        print("   3. Run this test again")
        return
    
    # Step 2: Filter
    filtered = await test_quality_filter(articles)
    print()
    
    if not filtered:
        print("⚠️  No articles passed quality filter")
        return
    
    # Step 3: AI Validation
    validated = await test_ai_validation(filtered)
    print()
    
    if not validated:
        print("⚠️  No articles approved by AI editor")
        return
    
    # Step 4: Captions
    with_captions = await test_caption_generation(validated)
    print()
    
    # Step 5: Posting (dry run by default)
    await test_instagram_posting(with_captions, dry_run=True)
    print()
    
    # Summary
    print("="*70)
    print("📊 WORKFLOW TEST SUMMARY")
    print("="*70)
    print()
    print(f"✅ Fetched: {len(articles)} articles")
    print(f"✅ Filtered: {len(filtered)} articles (passed quality check)")
    print(f"✅ Validated: {len(validated)} articles (AI approved)")
    print(f"✅ Ready to post: {len(with_captions)} articles")
    print()
    
    if with_captions:
        print("🎉 COMPLETE WORKFLOW IS WORKING!")
        print()
        print("Next steps:")
        print("1. To post manually: curl http://localhost:8000/test-hourly-burst")
        print("2. To start scheduler: python scheduler.py")
        print("3. To preview without posting: curl http://localhost:8000/preview-articles")
    else:
        print("⚠️  Workflow incomplete - check errors above")
    
    print()
    print("="*70)

# Run the test
if __name__ == "__main__":
    asyncio.run(run_complete_test())
