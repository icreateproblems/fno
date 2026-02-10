"""
Instagram Graph API Posting Script
Posts news stories to Instagram using official Graph API
"""
import os
import sys
import time
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BUSINESS_ACCOUNT_ID,
    INSTAGRAM_API_VERSION,
    OUTPUT_IMAGE_PATH,
    OUTPUT_IMAGE_SIZE,
    BODY_FONT_PATH,
    TITLE_FONT_PATH,
    MAX_POSTS_PER_HOUR_NORMAL,
    MAX_POSTS_PER_HOUR_BREAKING,
    MAX_POSTS_PER_DAY,
    BREAKING_NEWS_KEYWORDS
)
from app.logger import get_logger
from app.utils import format_error_message, is_nepali_text
from app.db import init_database
from app.db_pool import get_supabase_client
from app.content_safety import is_safe_to_post
from app.alerts import alert_manager
from app.env_validator import validate_and_exit_if_invalid

from groq_caption import generate_caption, rephrase_description_with_groq
from template_render import render_news_on_template
from content_filter import should_publish
from ai_content_monitor import AIContentMonitor
from utilities.upload_to_imgbb import upload_image_to_imgbb

load_dotenv()

logger = get_logger(__name__)

# Initialize AI content monitor
ai_monitor = AIContentMonitor()

# Font aliases
FONT_REGULAR = BODY_FONT_PATH
FONT_BOLD = TITLE_FONT_PATH

# Nepal timezone (UTC+5:45)
NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))


def should_post_now():
    """Check if we should post now (skip sleeping hours)"""
    if os.getenv('FORCE_POST') == 'true':
        logger.info("🧪 FORCE_POST enabled - bypassing random checks")
        return True
    
    nepal_time = datetime.now(NEPAL_TZ)
    current_hour = nepal_time.hour
    
    logger.info(f"Current Nepal time: {nepal_time.strftime('%Y-%m-%d %H:%M:%S')} (Hour: {current_hour})")
    
    # Skip sleeping hours (1am-6am Nepal time)
    if 1 <= current_hour < 6:
        logger.info(f"Sleeping hours (1-6am Nepal time) - skipping post")
        return False
    
    return True


def check_daily_limit(supabase):
    """Enforce max posts per day"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    try:
        posts_today = (
            supabase.table("posting_history")
            .select("id")
            .gte("created_at", today)
            .eq("success", True)
            .execute()
            .data
        )

        if len(posts_today) >= MAX_POSTS_PER_DAY:
            logger.info(f"Daily limit reached: {len(posts_today)}/{MAX_POSTS_PER_DAY} posts")
            return False

        logger.info(f"Daily posts: {len(posts_today)}/{MAX_POSTS_PER_DAY} - OK to continue")
        return True

    except Exception as e:
        logger.warning(f"Could not check daily limit: {e}")
        return True


def is_breaking_news(headline: str, description: str = "") -> bool:
    """Detect if a story is breaking news"""
    combined_text = f"{headline} {description}".lower()
    for keyword in BREAKING_NEWS_KEYWORDS:
        if keyword in combined_text:
            return True
    return False


def upload_image_to_instagram(image_path: str, caption: str) -> tuple:
    """
    Upload image to Instagram using Graph API (2-step process)
    
    IMPORTANT: Instagram Graph API requires a publicly accessible image URL.
    You have two options:
    
    1. Host images on a public server (S3, CloudFlare, etc.) - RECOMMENDED
    2. Use temporary public URL services (imgbb, etc.) - for testing only
    
    This implementation uses a placeholder approach. You MUST implement one of:
    - Upload to S3/CloudFlare and use that URL
    - Use a temporary hosting service for testing
    - Set up a public webhook endpoint to serve images
    
    Returns: (success: bool, media_id: str, error: str)
    """
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        return False, None, "Missing Instagram credentials"
    
    try:
        # Upload image to public hosting (imgbb for now)
        logger.info("📤 Uploading image to public host...")
        upload_success, image_url, upload_error = upload_image_to_imgbb(image_path, expiration=3600)
        
        if not upload_success:
            logger.error(f"❌ Failed to upload image: {upload_error}")
            return False, None, f"Image upload failed: {upload_error}"
        
        logger.info(f"✓ Image uploaded: {image_url}")
        
    except Exception as e:
        return False, None, f"Image upload error: {e}"
    
    try:
        # Step 1: Create media container with PUBLIC image URL
        logger.info("📤 Step 1: Creating Instagram media container...")
        
        create_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        
        params = {
            "image_url": image_url,  # MUST be publicly accessible
            "caption": caption[:2200],  # Instagram limit
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.post(create_url, data=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        container_id = result.get('id')
        
        if not container_id:
            return False, None, f"No container ID returned: {result}"
        
        logger.info(f"✓ Container created: {container_id}")
        
        # Wait for Instagram to process the image (recommended)
        logger.info("⏳ Waiting for Instagram to process image...")
        time.sleep(5)
        
        # Step 2: Publish the media container
        logger.info("📤 Step 2: Publishing to Instagram...")
        
        publish_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
        publish_data = {
            'creation_id': container_id,
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
        
        publish_response = requests.post(publish_url, data=publish_data, timeout=30)
        publish_response.raise_for_status()
        
        publish_result = publish_response.json()
        media_id = publish_result.get('id')
        
        if not media_id:
            return False, None, f"No media ID returned: {publish_result}"
        
        logger.info(f"✅ Published to Instagram: {media_id}")
        return True, media_id, None
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error: {e}"
        try:
            error_detail = e.response.json()
            error_msg = f"HTTP {e.response.status_code}: {error_detail}"
        except:
            pass
        logger.error(f"❌ Instagram upload failed: {error_msg}")
        return False, None, error_msg
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Instagram upload failed: {error_msg}")
        return False, None, error_msg


def main():
    """Main Instagram posting function using Graph API"""
    
    # Check for pause flag
    if os.getenv('PAUSE_POSTING', 'false').lower() == 'true':
        logger.info("⏸️  PAUSE_POSTING is enabled - exiting")
        return
    
    # Validate environment
    validate_and_exit_if_invalid()

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error(format_error_message("missing_env", "SUPABASE_URL / SUPABASE_KEY"))
        return
    
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        logger.error(format_error_message("missing_env", "INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ACCOUNT_ID"))
        return

    # Resolve template path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "templates", "breaking_template(1350).png")
    
    if not os.path.exists(template_path):
        logger.error(format_error_message("template_missing", template_path))
        return

    # Initialize database
    if not init_database(SUPABASE_URL, SUPABASE_KEY):
        return

    logger.info("Starting Instagram posting cycle (Graph API)...")
    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)

    # Check if should post now
    if not should_post_now():
        logger.info("Skipped this cycle (time-based check)")
        return

    # Check daily limit
    if not check_daily_limit(supabase):
        logger.info("Daily limit reached")
        return

    # Rate checks
    now = datetime.now()
    hour_ago = (now - timedelta(hours=1)).isoformat()

    try:
        posts_hour = (
            supabase.table("posting_history")
            .select("id")
            .gte("created_at", hour_ago)
            .eq("success", True)
            .execute()
            .data
        )
    except Exception as e:
        logger.warning(f"Could not check hourly rate: {e}")
        posts_hour = []

    # Get next validated, unposted story
    res = (
        supabase.table("stories")
        .select("*")
        .eq("is_validated", True)
        .eq("published", False)
        .order("published_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        logger.info(format_error_message("no_validated_stories", ""))
        return

    story = res.data[0]
    breaking = is_breaking_news(story["headline"], story.get("description", ""))

    if breaking:
        logger.info(f"🔥 BREAKING NEWS detected - using elevated rate limit")
    else:
        logger.info(f"📰 Normal news - using standard rate limit")

    max_posts_per_hour = MAX_POSTS_PER_HOUR_BREAKING if breaking else MAX_POSTS_PER_HOUR_NORMAL

    if len(posts_hour) >= max_posts_per_hour:
        msg = f"{len(posts_hour)}/{max_posts_per_hour} posts this hour"
        logger.info(format_error_message("rate_limited", msg))
        return

    # Content safety check
    safe, safety_score, safety_reason = is_safe_to_post(
        story["headline"],
        story.get("description", ""),
        story.get("source", "")
    )

    if not safe:
        logger.warning(f"⊘ Content safety violation: {story['headline'][:60]}... - {safety_reason}")
        
        supabase.table("stories").update({"published": True, "rejected": True}).eq("id", story["id"]).execute()
        supabase.table("posting_history").insert({
            "story_id": story["id"],
            "success": False,
            "platform": "instagram_graph",
            "error_message": f"Safety: {safety_reason}"
        }).execute()
        return

    # AI content evaluation
    logger.info("🤖 AI chatbot analyzing content...")
    ai_decision = ai_monitor.evaluate_content(
        story["headline"],
        story.get("description", ""),
        story.get("category", "general"),
        story.get("source", "")
    )
    
    logger.info(
        f"✅ AI chatbot decision: PUBLISH "
        f"(score: {ai_decision['score']}/100, ethics: {ai_decision['ethics_score']}, "
        f"engagement: {ai_decision['engagement_score']}) - {ai_decision['reasoning']}"
    )

    # Detect language and translate if needed
    combined_text = f"{story['headline']} {story.get('description', '')}"
    is_nepali = is_nepali_text(combined_text)
    target_language = "nepali_to_english" if is_nepali else "en"

    # Generate caption with proper structure
    caption_data = generate_caption(
        story["headline"],
        story.get("description", ""),
        story.get("category", "general"),
        language=target_language
    )
    
    # Format caption with clear structure:
    # Title (Headline)
    # Paragraph (Description)
    # Date
    # [Space]
    # Hashtags
    
    # Parse and format the published date
    date_str = ""
    if story.get("published_at"):
        try:
            pub_date = datetime.fromisoformat(story["published_at"].replace('Z', '+00:00'))
            date_str = pub_date.strftime("%B %d, %Y")
        except:
            date_str = datetime.now().strftime("%B %d, %Y")
    else:
        date_str = datetime.now().strftime("%B %d, %Y")
    
    # Get source
    source_str = f"Source: {story.get('source', 'Fast News')}" if story.get('source') else "Source: Fast News"
    
    # Get hashtags from caption generation
    hashtags = caption_data.get('hashtags', '').strip()

    # Rephrase description for image (concise, 2 sentences) and caption (detailed, 3-4 sentences)
    logger.info("📝 Generating content for image and caption...")
    
    # For image: concise 2-sentence summary that fits
    image_description = rephrase_description_with_groq(
        story["headline"],
        story.get("description", ""),
        language=target_language,
        for_image=True  # Request concise version
    )
    
    # For caption: detailed full context
    caption_description = rephrase_description_with_groq(
        story["headline"],
        story.get("description", ""),
        language=target_language,
        for_image=False  # Request detailed version
    )
    logger.info(f"✓ Image text: {image_description[:60]}...")
    logger.info(f"✓ Caption text: {caption_description[:60]}...")
    
    # Create English title from the image description (first sentence)
    # This ensures title is always in English, avoiding font rendering issues
    if '. ' in image_description[:120]:
        english_title = image_description[:image_description.index('. ', 0, 120) + 1].strip()
    else:
        # If no period found, use first 80 characters
        english_title = image_description[:80].strip() + ('...' if len(image_description) > 80 else '')
    
    # Clean Nepali title for caption
    nepali_title = story["headline"].strip()
    for prefix in ["BREAKING:", "UPDATE:", "URGENT:", "LIVE:", "LATEST:"]:
        if nepali_title.upper().startswith(prefix):
            nepali_title = nepali_title[len(prefix):].strip()
    
    # Caption: Nepali title + Detailed description + Source + Hashtags
    caption = f"{nepali_title}\n\n{caption_description}\n\n{source_str}\n\n{hashtags}"

    # Render image with English title and complete description
    output_path = OUTPUT_IMAGE_PATH
    render_news_on_template(
        template_path,
        english_title,
        image_description,
        output_path,
        title_font_path=FONT_BOLD,
        body_font_path=FONT_REGULAR,
        target_size=OUTPUT_IMAGE_SIZE,
        source=story.get("source", ""),
        published_at=story.get("published_at", ""),
    )

    if not os.path.exists(output_path):
        logger.error(format_error_message("render_failed", output_path))
        return

    # Upload to Instagram
    logger.info(f"📤 Posting to Instagram: {story['headline'][:50]}...")
    success, media_id, error = upload_image_to_instagram(output_path, caption)

    if success:
        logger.info(f"✅ Posted to Instagram: {media_id}")
        
        # Mark as published
        supabase.table("stories").update({
            "published": True,
            "posted_at": datetime.now().isoformat()
        }).eq("id", story["id"]).execute()

        # Log success
        supabase.table("posting_history").insert({
            "story_id": story["id"],
            "success": True,
            "platform": "instagram_graph",
            "post_id": media_id,
            "posted_at": datetime.now().isoformat()
        }).execute()

        logger.info("✓ Post cycle complete")
    else:
        logger.error(f"❌ Instagram post failed: {error}")
        
        # Log failure
        supabase.table("posting_history").insert({
            "story_id": story["id"],
            "success": False,
            "platform": "instagram_graph",
            "error_message": str(error)
        }).execute()


if __name__ == "__main__":
    main()
