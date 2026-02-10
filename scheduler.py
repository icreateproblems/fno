"""
Scheduler for automated Instagram posting.
Implements 2-3 posts/hour strategy during Nepal peak hours.
"""
import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import pytz

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from app.config import Config
from app.logger import get_logger
from app.db_pool import get_supabase_client
from quality_filter.content_processor import (
    generate_smart_caption, 
    relaxed_quality_filter,
    detect_content_category,
    get_category_emoji
)
from quality_filter.content_editor import validate_article, get_content_editor

# Import template rendering and image upload
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from scripts.template_render import render_news_on_template
from scripts.utilities.upload_to_imgbb import upload_image_bytes_to_imgbb

load_dotenv()

logger = get_logger(__name__)

# Nepal timezone
npt_tz = pytz.timezone('Asia/Kathmandu')

# Track daily category distribution
daily_category_stats = {}


async def get_today_posted_categories() -> List[str]:
    """
    Get list of categories posted today for diversity tracking.
    
    Returns:
        List of category names posted today
    """
    try:
        supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Get today's date range
        today_start = datetime.now(npt_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Fetch posts from today from 'stories' table
        response = supabase.table('stories')\
            .select('category')\
            .eq('posted', True)\
            .gte('posted_at', today_start.isoformat())\
            .execute()
        
        categories = [row.get('category', 'general') for row in response.data if row.get('category')]
        return categories
        
    except Exception as e:
        logger.warning(f"Could not fetch today's categories: {e}")
        return []


async def fetch_rss_articles(limit: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch articles from Supabase that haven't been posted yet.
    
    Args:
        limit: Maximum number of articles to fetch
        
    Returns:
        List of article dictionaries
    """
    try:
        supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Fetch unposted stories from 'stories' table (no image requirement)
        response = supabase.table('stories')\
            .select('*')\
            .eq('posted', False)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        articles = []
        for story in response.data:
            # Calculate age in hours - handle various timestamp formats
            created_at_str = story['created_at']
            try:
                # Normalize timestamp: pad microseconds to 6 digits if needed
                import re
                # Match timestamp with optional microseconds and timezone
                match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})?', created_at_str)
                if match:
                    dt_part, micros, tz = match.groups()
                    # Pad or truncate microseconds to 6 digits
                    if micros:
                        micros = micros.ljust(6, '0')[:6]  # Pad with zeros or truncate
                        dt_part = f"{dt_part}.{micros}"
                    # Add timezone if missing
                    if not tz:
                        tz = '+00:00'
                    elif tz == 'Z':
                        tz = '+00:00'
                    
                    normalized = f"{dt_part}{tz}"
                    created_at = datetime.fromisoformat(normalized)
                else:
                    # Fallback to current time
                    logger.warning(f"Could not parse timestamp: {created_at_str}, using current time")
                    created_at = datetime.now(pytz.UTC)
            except Exception as e:
                logger.warning(f"Error parsing timestamp '{created_at_str}': {e}, using current time")
                created_at = datetime.now(pytz.UTC)
            
            # Ensure created_at is timezone aware
            if created_at.tzinfo is None:
                created_at = pytz.UTC.localize(created_at)
            
            age_hours = (datetime.now(pytz.UTC) - created_at).total_seconds() / 3600
            
            articles.append({
                'id': story.get('id'),
                'title': story.get('headline', ''),
                'summary': story.get('description', ''),
                'content': story.get('description', ''),
                'source': story.get('source', 'FastNews'),
                'image': story.get('image_url', ''),
                'url': story.get('url', ''),
                'age_hours': age_hours
            })
        
        logger.info(f"Fetched {len(articles)} unposted articles from database")
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return []


async def publish_instagram_graph(
    caption: str,
    story_id: int = None,
    category: str = 'general',
    article: Dict[str, Any] = None,
    title: str = None,
    summary: str = None,
    source: str = None,
    published_at: str = None
) -> bool:
    """
    Publish to Instagram using Graph API with template rendering.
    
    Args:
        caption: Instagram caption
        story_id: Database story ID to mark as posted
        category: Content category for tracking
        article: Article dict with title, description, source, etc. (preferred)
        title: Article title (if article dict not provided)
        summary: Article summary/description (if article dict not provided)
        source: Article source (if article dict not provided)
        published_at: Publication date (if article dict not provided)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        
        # Build article dict if individual params provided
        if not article:
            article = {
                'title': title or 'FastNews.org',
                'headline': title or 'FastNews.org', 
                'description': summary or '',
                'summary': summary or '',
                'source': source or 'FastNews.org',
                'published_at': published_at or '',
                'pubDate': published_at or ''
            }
        
        # Get article text for rendering
        headline = article.get('title', article.get('headline', 'FastNews.org'))
        description = article.get('description', article.get('summary', ''))
        source = article.get('source', 'FastNews.org')
        published_at = article.get('published_at', article.get('pubDate', ''))
        
        # Prepare English title from headline (clean it up)
        english_title = headline.strip()
        for prefix in ["BREAKING:", "UPDATE:", "URGENT:", "LIVE:", "LATEST:"]:
            if english_title.upper().startswith(prefix):
                english_title = english_title[len(prefix):].strip()
        
        # Use first sentence for image if description is too long
        image_description = description
        if len(image_description) > 150:
            # Try to find first sentence
            period_idx = image_description.find('. ')
            if period_idx > 0:
                image_description = image_description[:period_idx + 1]
            else:
                image_description = image_description[:150] + '...'
        
        # Template paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, Config.TEMPLATE_PATH)
        output_path = os.path.join(base_dir, Config.OUTPUT_IMAGE_PATH)
        title_font = os.path.join(base_dir, Config.TITLE_FONT_PATH)
        body_font = os.path.join(base_dir, Config.BODY_FONT_PATH)
        
        # Render article onto template
        logger.info(f"🎨 Rendering: {english_title[:50]}...")
        render_news_on_template(
            template_path,
            english_title,
            image_description,
            output_path,
            title_font_path=title_font,
            body_font_path=body_font,
            target_size=Config.OUTPUT_IMAGE_SIZE,
            source=source,
            published_at=published_at
        )
        
        # Check if render was successful
        if not os.path.exists(output_path):
            logger.error(f"Template rendering failed - output file not created")
            return False
        
        # Upload rendered image to ImgBB
        imgbb_key = Config.IMGBB_API_KEY or os.getenv('IMGBB_API_KEY')
        if not imgbb_key:
            logger.error("ImgBB API key not configured")
            return False
        
        # Read rendered image
        with open(output_path, 'rb') as f:
            image_bytes = f.read()
        
        logger.info(f"📤 Uploading rendered image to ImgBB ({len(image_bytes)} bytes)...")
        image_url = upload_image_bytes_to_imgbb(image_bytes, imgbb_key)
        
        if not image_url:
            logger.error("Failed to upload rendered image to ImgBB")
            return False
        
        logger.info(f"✅ Image uploaded: {image_url[:60]}...")
        
        # Instagram Graph API posting
        access_token = Config.GRAPH_TOKEN or Config.INSTAGRAM_ACCESS_TOKEN
        account_id = Config.INSTAGRAM_BUSINESS_ACCOUNT_ID
        
        if not access_token or not account_id:
            logger.error("Missing Instagram credentials")
            return False
        
        # Step 1: Create container
        create_url = f"https://graph.facebook.com/{Config.INSTAGRAM_API_VERSION}/{account_id}/media"
        create_payload = {
            'image_url': image_url,
            'caption': caption,
            'access_token': access_token
        }
        
        create_response = requests.post(create_url, data=create_payload, timeout=30)
        
        if create_response.status_code != 200:
            logger.error(f"Failed to create container: {create_response.text}")
            return False
        
        container_id = create_response.json().get('id')
        
        # Step 2: Publish container
        publish_url = f"https://graph.facebook.com/{Config.INSTAGRAM_API_VERSION}/{account_id}/media_publish"
        publish_payload = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_payload, timeout=30)
        
        if publish_response.status_code != 200:
            logger.error(f"Failed to publish: {publish_response.text}")
            return False
        
        # Mark as posted in database with category
        if story_id:
            try:
                supabase = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                supabase.table('stories')\
                    .update({
                        'posted': True, 
                        'posted_at': datetime.now(pytz.UTC).isoformat(),
                        'category': category
                    })\
                    .eq('id', story_id)\
                    .execute()
            except Exception as e:
                logger.warning(f"Failed to update database: {e}")
        
        logger.info(f"✅ Successfully posted to Instagram (container: {container_id})")
        
        # Clean up temp file
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"Instagram posting error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def hourly_publish_burst():
    """
    Execute 2-3 posts/hour with AI editor validation and category diversity.
    Now targets 30-40 posts/day with content from multiple categories.
    """
    current_time = datetime.now(npt_tz)
    logger.info(f"🚀 {current_time} - Starting hourly burst (target {Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX} posts)")
    
    # Get today's posted categories for diversity
    posted_categories = await get_today_posted_categories()
    editor = get_content_editor()
    
    # Log category balance
    if posted_categories:
        balance = editor.get_category_balance(posted_categories)
        logger.info(f"📊 Today's stats: {balance['total']} posts - {balance['counts']}")
        if balance['needs_more']:
            logger.info(f"🎯 Need more: {balance['needs_more']}")
    
    # Fetch more articles for better selection
    articles = await fetch_rss_articles(limit=25)
    
    if not articles:
        logger.warning("No articles available for posting")
        return
    
    published = 0
    attempts = 0
    max_attempts = len(articles)
    
    for article in articles:
        attempts += 1
        
        # Debug: Check article structure
        logger.info(f"📋 Processing: {article.get('title', '')[:60]} - Has image: {bool(article.get('image'))}")
        
        # Apply relaxed quality filter first (fast)
        if not relaxed_quality_filter(article):
            content_len = len(article.get('content', article.get('description', '')))
            age = article.get('age_hours', 999)
            title_len = len(article.get('title', ''))
            logger.info(f"❌ Filtered: {article.get('title', '')[:50]} (content:{content_len} chars, age:{age:.1f}h, title:{title_len} chars)")
            continue
        
        # Detect preliminary category (before AI validation)
        preliminary_category = detect_content_category(
            article['title'], 
            article['summary']
        )
        
        # AI Editor Validation - the final decider!
        should_publish, category, metadata = validate_article(
            title=article['title'],
            summary=article['summary'],
            source=article['source'],
            content=article.get('content', '')
        )
        
        if not should_publish:
            logger.info(f"❌ Editor rejected: {article['title'][:50]} - {metadata.get('reason')}")
            continue
        
        # Check if we need diversity (prioritize underrepresented categories)
        needs_more_categories = editor.get_category_balance(posted_categories).get('needs_more', {})
        if needs_more_categories and category not in needs_more_categories:
            # We have underrepresented categories - skip if this isn't one
            if len(posted_categories) > 10:  # Only enforce after 10 posts
                logger.debug(f"⏭️ Skipping {category} - need more {list(needs_more_categories.keys())}")
                continue
        
        # Generate smart caption with category emoji
        category_emoji = get_category_emoji(category)
        caption = generate_smart_caption(
            article['title'],
            article['summary'],
            article['source']
        )
        # Add category emoji at start
        caption = f"{category_emoji} {caption}"
        
        # Attempt to publish (now using template rendering)
        success = await publish_instagram_graph(
            article=article,
            caption=caption,
            story_id=article.get('id'),
            category=category
        )
        
        if success:
            published += 1
            posted_categories.append(category)  # Track for diversity
            logger.info(
                f"✅ Published {published}/{Config.POSTS_PER_HOUR_MAX} "
                f"[{category.upper()}]: {article['title'][:50]}... "
                f"(Score: {metadata.get('score')}/100)"
            )
            
            # Stop after reaching max posts per burst
            if published >= Config.POSTS_PER_HOUR_MAX:
                break
            
            # Small delay between posts
            await asyncio.sleep(5)
    
    # Log final summary
    logger.info(
        f"✅ Burst complete: Published {published} posts from {attempts} candidates "
        f"({(published/attempts*100):.1f}% approval rate)"
    )


def start_scheduler():
    """
    Start the APScheduler with Nepal timezone and peak hour slots.
    """
    scheduler = AsyncIOScheduler(timezone=npt_tz)
    
    # Schedule jobs for each publish hour
    for hour in Config.PUBLISH_HOURS:
        scheduler.add_job(
            hourly_publish_burst,
            'cron',
            hour=hour,
            minute=Config.PUBLISH_MINUTE,
            id=f'publish_{hour:02d}:{Config.PUBLISH_MINUTE:02d}'
        )
        logger.info(f"Scheduled job for {hour:02d}:{Config.PUBLISH_MINUTE:02d} NPT")
    
    scheduler.start()
    logger.info(f"🕐 Scheduler started - {len(Config.PUBLISH_HOURS)} daily time slots configured")
    logger.info(f"📅 Publish times (NPT): {', '.join([f'{h:02d}:{Config.PUBLISH_MINUTE:02d}' for h in Config.PUBLISH_HOURS])}")
    
    return scheduler


if __name__ == "__main__":
    logger.info("=== Starting FastNewsOrg Scheduler ===")
    logger.info(f"Target: {Config.POSTS_PER_HOUR_MIN}-{Config.POSTS_PER_HOUR_MAX} posts/hour")
    logger.info(f"Daily cap: {Config.DAILY_CAP} posts")
    
    scheduler = start_scheduler()
    
    # Keep scheduler running
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
        scheduler.shutdown()
