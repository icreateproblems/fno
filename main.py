"""
FastAPI Main Application for FastNewsOrg
Provides test endpoints and health monitoring for Instagram posting.
"""
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import pytz
from dotenv import load_dotenv

from app.config import Config
from app.logger import get_logger
from scheduler import hourly_publish_burst, fetch_rss_articles, get_today_posted_categories
from quality_filter.content_processor import (
    is_nepali_text, 
    generate_smart_caption,
    detect_content_category,
    get_category_emoji
)
from quality_filter.content_editor import get_content_editor, validate_article

load_dotenv()

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FastNewsOrg API",
    description="Automated Instagram news posting with AI editor and category diversity (30-40 posts/day)",
    version="3.0.0"
)

# Nepal timezone
npt_tz = pytz.timezone('Asia/Kathmandu')


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "app": "FastNewsOrg",
        "version": "3.0.0",
        "status": "running",
        "target": f"{Config.DAILY_POST_TARGET_MIN}-{Config.DAILY_POST_TARGET_MAX} posts/day",
        "posts_per_hour": f"{Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX}",
        "features": [
            "AI Editor Validation (GROQ)",
            "Category Diversity Tracking",
            "Native Nepali/English Captions",
            "15 Daily Time Slots"
        ],
        "categories": Config.CONTENT_CATEGORIES,
        "endpoints": {
            "/health": "Health check",
            "/test-hourly-burst": "Manual test - publish 2-3 posts with AI validation",
            "/config": "View current configuration",
            "/preview-articles": "Preview articles with AI editor scores",
            "/category-stats": "View today's category distribution",
            "/stats": "Database statistics"
        }
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns current status and configuration.
    """
    current_time = datetime.now(npt_tz)
    
    return {
        "status": "healthy",
        "timestamp": current_time.isoformat(),
        "timezone": "Asia/Kathmandu",
        "target": f"{Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX}/hour",
        "daily_cap": Config.DAILY_CAP,
        "publish_hours": Config.PUBLISH_HOURS,
        "publish_minute": Config.PUBLISH_MINUTE,
        "next_scheduled": f"{Config.PUBLISH_HOURS[0]:02d}:{Config.PUBLISH_MINUTE:02d} NPT"
    }


@app.get("/test-hourly-burst")
async def test_burst():
    """
    Manual test endpoint - triggers hourly burst immediately.
    Should publish 2-3 clean posts with native Nepali/English captions.
    """
    logger.info("Manual burst test triggered via API")
    
    try:
        await hourly_publish_burst()
        
        return {
            "status": "burst_complete",
            "expected": f"{Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX} posts",
            "message": "Check Instagram for new posts with clean Nepali/English captions",
            "timestamp": datetime.now(npt_tz).isoformat()
        }
    except Exception as e:
        logger.error(f"Burst test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """
    View current configuration settings.
    """
    return {
        "posting": {
            "daily_target_min": Config.DAILY_POST_TARGET_MIN,
            "daily_target_max": Config.DAILY_POST_TARGET_MAX,
            "posts_per_hour_min": Config.POSTS_PER_HOUR_MIN,
            "posts_per_hour_max": Config.POSTS_PER_HOUR_MAX,
            "daily_cap": Config.DAILY_CAP,
            "publish_hours": Config.PUBLISH_HOURS,
            "publish_minute": Config.PUBLISH_MINUTE,
            "total_daily_slots": len(Config.PUBLISH_HOURS)
        },
        "categories": {
            "available": Config.CONTENT_CATEGORIES,
            "min_posts_per_day": Config.CATEGORY_MIN_POSTS_PER_DAY
        },
        "filters": {
            "min_length_chars": Config.MIN_LENGTH_CHARS,
            "max_length_chars": Config.MAX_LENGTH_CHARS,
            "max_age_hours": Config.MAX_AGE_HOURS,
            "min_completeness": Config.MIN_COMPLETENESS
        },
        "ai_editor": {
            "enabled": bool(Config.GROQ_EDITOR_API_KEY),
            "model": Config.GROQ_EDITOR_MODEL,
            "temperature": Config.GROQ_EDITOR_TEMPERATURE
        },
        "rss_feeds": {
            "total": len(Config.RSS_FEEDS),
            "nepali_sources": [url for url in Config.RSS_FEEDS if any(
                nepali in url for nepali in ['ekantipur', 'setopati', 'onlinekhabar', 'ratopati', 'nepali']
            )],
            "english_sources": [url for url in Config.RSS_FEEDS if 'bbc' in url or 'cnn' in url]
        },
        "instagram": {
            "api_version": Config.INSTAGRAM_API_VERSION,
            "has_access_token": bool(Config.INSTAGRAM_ACCESS_TOKEN),
            "has_business_account_id": bool(Config.INSTAGRAM_BUSINESS_ACCOUNT_ID)
        }
    }


@app.get("/preview-articles")
async def preview_articles(limit: int = 10, use_ai_editor: bool = True):
    """
    Preview available articles with AI editor validation scores.
    Shows what would be posted with generated captions and categories.
    
    Args:
        limit: Number of articles to preview (default 10)
        use_ai_editor: Whether to run AI editor validation (default True)
    """
    try:
        articles = await fetch_rss_articles(limit=limit)
        
        previews = []
        for article in articles:
            # Detect category
            preliminary_category = detect_content_category(
                article['title'], 
                article['summary']
            )
            
            # AI Editor validation if enabled
            if use_ai_editor:
                should_publish, category, metadata = validate_article(
                    article['title'],
                    article['summary'],
                    article['source'],
                    article.get('content', '')
                )
            else:
                should_publish = True
                category = preliminary_category
                metadata = {'score': 70, 'reason': 'AI validation skipped'}
            
            # Generate caption
            category_emoji = get_category_emoji(category)
            caption = generate_smart_caption(
                article['title'],
                article['summary'],
                article['source']
            )
            caption = f"{category_emoji} {caption}"
            
            previews.append({
                "title": article['title'],
                "source": article['source'],
                "category": category,
                "category_emoji": category_emoji,
                "caption": caption,
                "is_nepali": is_nepali_text(article['title']),
                "age_hours": article.get('age_hours', 0),
                "has_image": bool(article.get('image')),
                "ai_editor": {
                    "approved": should_publish,
                    "score": metadata.get('score', 0),
                    "reason": metadata.get('reason', ''),
                    "interest_level": metadata.get('interest_level', 'unknown')
                }
            })
        
        # Calculate approval stats
        approved_count = sum(1 for p in previews if p['ai_editor']['approved'])
        
        return {
            "total_articles": len(previews),
            "approved_count": approved_count,
            "approval_rate": f"{(approved_count/len(previews)*100):.1f}%" if previews else "0%",
            "articles": previews,
            "timestamp": datetime.now(npt_tz).isoformat()
        }
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/category-stats")
async def get_category_stats():
    """
    Get today's category distribution and diversity metrics.
    Shows which categories have been posted and which need more content.
    """
    try:
        # Get today's posted categories
        posted_categories = await get_today_posted_categories()
        
        # Get category balance from editor
        editor = get_content_editor()
        balance = editor.get_category_balance(posted_categories)
        
        # Calculate category breakdown
        from collections import Counter
        category_counts = Counter(posted_categories)
        
        # Build category breakdown with emojis
        category_breakdown = []
        for category in Config.CONTENT_CATEGORIES:
            count = category_counts.get(category, 0)
            target = Config.CATEGORY_MIN_POSTS_PER_DAY.get(category, 0)
            emoji = get_category_emoji(category)
            
            category_breakdown.append({
                "category": category,
                "emoji": emoji,
                "count": count,
                "target": target,
                "percentage": f"{(count/len(posted_categories)*100):.1f}%" if posted_categories else "0%",
                "status": "✅" if count >= target else "⚠️" if count > 0 else "❌"
            })
        
        return {
            "date": datetime.now(npt_tz).date().isoformat(),
            "total_posts_today": len(posted_categories),
            "target_range": f"{Config.DAILY_POST_TARGET_MIN}-{Config.DAILY_POST_TARGET_MAX}",
            "progress": f"{(len(posted_categories)/Config.DAILY_POST_TARGET_MIN*100):.1f}%",
            "categories": category_breakdown,
            "needs_more": balance.get('needs_more', {}),
            "most_posted": balance.get('most_posted', None),
            "diversity_score": f"{(len(set(posted_categories))/len(Config.CONTENT_CATEGORIES)*100):.1f}%",
            "timestamp": datetime.now(npt_tz).isoformat()
        }
    except Exception as e:
        logger.error(f"Category stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get posting statistics from database.
    """
    try:
        from app.db_pool import get_supabase_client
        
        supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Count total stories
        total_response = supabase.table('raw_stories').select('id', count='exact').execute()
        total_stories = total_response.count
        
        # Count posted stories
        posted_response = supabase.table('raw_stories')\
            .select('id', count='exact')\
            .eq('posted', True)\
            .execute()
        posted_stories = posted_response.count
        
        # Count unposted stories
        unposted_stories = total_stories - posted_stories
        
        return {
            "total_stories": total_stories,
            "posted_stories": posted_stories,
            "unposted_stories": unposted_stories,
            "posting_rate": f"{(posted_stories / total_stories * 100):.1f}%" if total_stories > 0 else "0%",
            "timestamp": datetime.now(npt_tz).isoformat()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/manual-post")
async def manual_post(title: str, summary: str, source: str, image_url: str):
    """
    Manually post a single article to Instagram.
    
    Args:
        title: Article title
        summary: Article summary
        source: News source name
        image_url: Public URL of image
    """
    try:
        from scheduler import publish_instagram_graph
        
        caption = generate_smart_caption(title, summary, source)
        
        success = await publish_instagram_graph(image_url, caption)
        
        if success:
            return {
                "status": "success",
                "message": "Posted to Instagram",
                "caption": caption,
                "timestamp": datetime.now(npt_tz).isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to post to Instagram")
            
    except Exception as e:
        logger.error(f"Manual post failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    logger.info("=== Starting FastNewsOrg API ===")
    logger.info(f"Target: {Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX} posts/hour")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
