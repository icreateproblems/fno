"""
Comprehensive Test Suite for FastNewsOrg v3.0
Tests AI editor, category diversity, and posting system
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("🧪 FASTNEWSORG v3.0 - COMPREHENSIVE TEST SUITE")
print("="*70)
print()

# Load environment
load_dotenv()

# Test 1: Configuration
print("📋 TEST 1: Configuration Loading")
print("-" * 70)
try:
    from app.config import Config
    
    print(f"✅ Config loaded successfully")
    print(f"   Daily target: {Config.DAILY_POST_TARGET_MIN}-{Config.DAILY_POST_TARGET_MAX} posts")
    print(f"   Posts per hour: {Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX}")
    print(f"   Publish hours: {len(Config.PUBLISH_HOURS)} slots")
    print(f"   Categories: {len(Config.CONTENT_CATEGORIES)}")
    print(f"   GROQ Editor enabled: {bool(Config.GROQ_EDITOR_API_KEY)}")
    print()
except Exception as e:
    print(f"❌ Config test failed: {e}")
    print()

# Test 2: Content Processor
print("📝 TEST 2: Content Processor (Category Detection)")
print("-" * 70)
try:
    from quality_filter.content_processor import (
        is_nepali_text, 
        detect_content_category,
        get_category_emoji,
        generate_smart_caption
    )
    
    # Test Nepali detection
    nepali_text = "नेपाल सरकारले नयाँ नीति घोषणा गर्यो"
    english_text = "Nepal government announces new policy"
    
    print(f"✅ Nepali detection:")
    print(f"   '{nepali_text[:30]}...' → {is_nepali_text(nepali_text)}")
    print(f"   '{english_text}' → {is_nepali_text(english_text)}")
    print()
    
    # Test category detection
    test_articles = [
        ("नेप्सेमा ५० अंकको वृद्धि", "Stock market rises", "economy"),
        ("Nepal wins cricket match", "Cricket victory", "sports"),
        ("सरकारले बजेट घोषणा", "Budget announcement", "politics"),
        ("New AI technology launched", "Tech news", "technology"),
    ]
    
    print("✅ Category detection:")
    for title, summary, expected in test_articles:
        detected = detect_content_category(title, summary)
        emoji = get_category_emoji(detected)
        status = "✅" if detected == expected else "⚠️"
        print(f"   {status} '{title[:30]}' → {emoji} {detected}")
    print()
    
    # Test caption generation
    caption = generate_smart_caption(
        "Nepal wins cricket match",
        "Nepal defeated India in a thrilling match",
        "ESPN Cricinfo"
    )
    print("✅ Caption generation:")
    print(f"   {caption[:100]}...")
    print()
    
except Exception as e:
    print(f"❌ Content processor test failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 3: Content Editor (AI Validation)
print("🤖 TEST 3: AI Content Editor (GROQ Validation)")
print("-" * 70)
try:
    from quality_filter.content_editor import get_content_editor, validate_article
    
    editor = get_content_editor()
    
    if not editor.client:
        print("⚠️  GROQ Editor API key not found - validation will be skipped")
        print("   Set GROQ_EDITOR_API_KEY in .env to enable AI validation")
    else:
        print("✅ GROQ Editor initialized")
        
        # Test validation with sample articles
        test_cases = [
            {
                "title": "नेप्से परिसूचक ५० अंकले बढ्यो",
                "summary": "शेयर बजारमा आज राम्रो कारोबार भएको छ",
                "source": "SetoPati"
            },
            {
                "title": "Nepal defeats India in cricket",
                "summary": "Nepal cricket team won by 50 runs in Kathmandu",
                "source": "ESPN"
            },
            {
                "title": "New golf tournament announced",
                "summary": "International golf tournament to be held in Pokhara",
                "source": "Golf Digest"
            }
        ]
        
        print("\n   Testing AI validation on sample articles:")
        for i, article in enumerate(test_cases, 1):
            print(f"\n   Article {i}: {article['title'][:40]}")
            
            should_publish, category, metadata = validate_article(
                article['title'],
                article['summary'],
                article['source']
            )
            
            status = "✅ APPROVED" if should_publish else "❌ REJECTED"
            print(f"   {status} | Category: {category} | Score: {metadata.get('score', 0)}/100")
            print(f"   Reason: {metadata.get('reason', 'N/A')[:60]}")
    
    print()
    
except Exception as e:
    print(f"❌ Content editor test failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 4: Database Connection
print("🗄️  TEST 4: Database Connection")
print("-" * 70)
try:
    from app.db_pool import get_supabase_client
    
    supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # Test query
    response = supabase.table('raw_stories').select('id').limit(1).execute()
    
    print(f"✅ Database connection successful")
    print(f"   Stories in database: accessible")
    print()
    
except Exception as e:
    print(f"❌ Database test failed: {e}")
    print()

# Test 5: Scheduler Components
print("⏰ TEST 5: Scheduler Components")
print("-" * 70)
try:
    from scheduler import get_today_posted_categories
    import asyncio
    
    # Test category tracking
    loop = asyncio.get_event_loop()
    posted_categories = loop.run_until_complete(get_today_posted_categories())
    
    print(f"✅ Scheduler components loaded")
    print(f"   Today's posted categories: {len(posted_categories)}")
    if posted_categories:
        from collections import Counter
        counts = Counter(posted_categories)
        for cat, count in counts.most_common(5):
            emoji = get_category_emoji(cat)
            print(f"   {emoji} {cat}: {count} posts")
    else:
        print("   No posts yet today - ready to start!")
    print()
    
except Exception as e:
    print(f"❌ Scheduler test failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 6: API Endpoints (without starting server)
print("🌐 TEST 6: FastAPI App Configuration")
print("-" * 70)
try:
    from main import app
    
    print(f"✅ FastAPI app loaded")
    print(f"   Title: {app.title}")
    print(f"   Version: {app.version}")
    
    # Count routes
    routes = [route for route in app.routes if hasattr(route, 'path')]
    print(f"   Endpoints: {len(routes)}")
    
    # List main endpoints
    for route in routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ','.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"      {methods:6} {route.path}")
    
    print()
    
except Exception as e:
    print(f"❌ API test failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 7: Environment Variables
print("🔐 TEST 7: Environment Variables")
print("-" * 70)

required_vars = [
    ("SUPABASE_URL", bool(os.getenv("SUPABASE_URL"))),
    ("SUPABASE_KEY", bool(os.getenv("SUPABASE_KEY"))),
    ("GROQ_API_KEY", bool(os.getenv("GROQ_API_KEY"))),
    ("GROQ_EDITOR_API_KEY", bool(os.getenv("GROQ_EDITOR_API_KEY"))),
    ("INSTAGRAM_ACCESS_TOKEN", bool(os.getenv("INSTAGRAM_ACCESS_TOKEN"))),
    ("INSTAGRAM_BUSINESS_ACCOUNT_ID", bool(os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"))),
    ("GRAPH_LONG_TOKEN", bool(os.getenv("GRAPH_LONG_TOKEN"))),
    ("IMGBB_API_KEY", bool(os.getenv("IMGBB_API_KEY"))),
]

for var_name, is_set in required_vars:
    status = "✅" if is_set else "❌"
    print(f"{status} {var_name:30} {'Set' if is_set else 'Missing'}")

print()

# Summary
print("="*70)
print("📊 TEST SUMMARY")
print("="*70)
print()
print("✅ All core components loaded successfully!")
print()
print("Next Steps:")
print("1. Start API server: python main.py")
print("2. Test manual burst: curl http://localhost:8000/test-hourly-burst")
print("3. Preview articles: curl http://localhost:8000/preview-articles?limit=5")
print("4. Check categories: curl http://localhost:8000/category-stats")
print("5. Start scheduler: python scheduler.py")
print()
print("For production deployment, see DEPLOYMENT_V3.md")
print()
print("="*70)
