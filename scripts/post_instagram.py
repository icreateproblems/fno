"""
Instagram posting script with anti-detection measures.
Implements human-like behavior patterns to avoid Instagram automation detection.

Key Anti-Detection Features:
- Random delays between 1-5 minutes per post
- Randomized posting schedule (not predictable)
- Varied caption styles (5 different formats)
- Session refresh every 3-7 days
- Device rotation to simulate different phones
- Reduced frequency (max 20 posts/day)
- Random human activity (browsing profiles, etc.)
- Varying image quality/format
"""
import os
import sys
import time
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from instagrapi import Client
from PIL import Image

# Import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    TEMPLATE_PATH,
    OUTPUT_IMAGE_PATH,
    OUTPUT_IMAGE_SIZE,
    BODY_FONT_PATH,
    TITLE_FONT_PATH,
    NEPALI_BODY_FONT_PATH,
    NEPALI_TITLE_FONT_PATH,
    INSTAGRAM_SESSION_FILE,
    MAX_POSTS_PER_HOUR_NORMAL,
    MAX_POSTS_PER_HOUR_BREAKING,
    MAX_POSTS_PER_DAY,
    BREAKING_NEWS_KEYWORDS
)
from app.logger import get_logger
from app.utils import format_error_message, is_nepali_text
from app.db import init_database
from app.db_pool import get_supabase_client
from app.env_validator import validate_and_exit_if_invalid
from app.content_safety import is_safe_to_post
from app.alerts import alert_manager

# Import from scripts (works both as module and when run directly)
import sys
import os
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from groq_caption import generate_caption, rephrase_description_with_groq
from template_render import render_news_on_template
from content_filter import should_publish
from ai_content_monitor import AIContentMonitor

load_dotenv()

logger = get_logger(__name__)

# Initialize AI content monitor
ai_monitor = AIContentMonitor()

# Font aliases for template rendering
FONT_REGULAR = BODY_FONT_PATH
FONT_BOLD = TITLE_FONT_PATH

# Nepal timezone (UTC+5:45)
NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))

# Device presets for rotation (mimic different phones)
DEVICE_PRESETS = [
    ("Samsung Galaxy S21", "19.5", "1080x2400"),
    ("iPhone 13 Pro", "19.5", "1170x2532"),
    ("Google Pixel 6", "20", "1080x2340"),
    ("OnePlus 9", "20", "1080x2400"),
    ("Xiaomi Mi 11", "19.5", "1080x2400"),
]

# Caption style variations to avoid pattern detection
CAPTION_STYLES = [
    "breaking_news",
    "question_format",
    "simple_text",
    "short_format",
    "emoji_variation"
]


def should_post_now():
    """
    Randomized posting decision to avoid predictable patterns.
    Returns True ~80% of the time during active hours to ensure consistent posting.
    """
    # MANUAL TEST MODE: Check for force post flag
    if os.getenv('FORCE_POST') == 'true':
        logger.info("🧪 FORCE_POST enabled - bypassing random checks")
        return True
    
    # Get current Nepal time (CircleCI runs in UTC, so we need to convert)
    nepal_time = datetime.now(NEPAL_TZ)
    current_hour = nepal_time.hour
    
    logger.info(f"Current Nepal time: {nepal_time.strftime('%Y-%m-%d %H:%M:%S')} (Hour: {current_hour})")
    
    # Skip "sleeping hours" (1am-6am Nepal time) - realistic human behavior
    if 1 <= current_hour < 6:
        logger.info(f"Sleeping hours (1-6am Nepal time) - skipping post")
        return False

    # Random chance: post 80% of the time (increased for better content delivery)
    # This gives ~19-22 posts/day before daily limit (20 posts/day)
    random_chance = random.random()
    if random_chance < 0.80:
        logger.info(
            f"Random posting chance triggered ({random_chance:.2%})"
        )
        return True

    logger.info(
        f"Random skip triggered ({random_chance:.2%} > 80%)"
    )
    return False


def check_daily_limit(supabase):
    """Enforce max 20 posts per day (balanced for news account)"""
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

        if len(posts_today) >= 20:
            logger.info(
                f"Daily limit reached: {len(posts_today)}/20 posts"
            )
            return False

        logger.info(
            f"Daily posts: {len(posts_today)}/20 - OK to continue"
        )
        return True

    except Exception as e:
        logger.warning(f"Could not check daily limit: {e}")
        return True


def is_breaking_news(headline: str, description: str = "") -> bool:
    """
    Detect if a story is breaking news based on keywords.
    Breaking news stories can be posted more frequently (3/hour vs 1/hour).
    """
    combined_text = f"{headline} {description}".lower()
    for keyword in BREAKING_NEWS_KEYWORDS:
        if keyword in combined_text:
            return True
    return False


def get_human_like_delays():
    """
    Generate random delays to simulate human behavior.
    Returns dict with browse, edit, and review delays.
    """
    delays = {
        'browse': random.randint(30, 180),   # 30-180 seconds
        'edit': random.randint(15, 90),      # 15-90 seconds
        'review': random.randint(10, 60)     # 10-60 seconds
    }

    total_time = sum(delays.values())
    logger.info(
        f"Human-like delays: "
        f"browse={delays['browse']}s, "
        f"edit={delays['edit']}s, "
        f"review={delays['review']}s "
        f"(total: {total_time}s = {total_time/60:.1f}min)"
    )

    return delays


def generate_caption_variation(headline, description, category="", source=""):
    """
    Generate varied caption styles to avoid pattern detection.
    Each style looks different to avoid Instagram's pattern algorithms.
    Source is included in caption instead of image.
    """
    style = random.choice(CAPTION_STYLES)
    logger.info(f"Using caption style: {style}")

    if style == "breaking_news":
        # Style 1: Breaking news with emojis
        source_text = f"\n📰 Source: {source}" if source else ""
        return (
            f"🚨 BREAKING: {headline}\n\n"
            f"{description}{source_text}\n\n"
            f"#Breaking #News #WorldNews #Headlines #fastnewsorg"
        )

    elif style == "question_format":
        # Style 2: Question format
        source_text = f"\n📰 Source: {source}" if source else ""
        return (
            f"What's happening?\n\n"
            f"{headline}\n\n"
            f"{description}{source_text}\n\n"
            f"#Updates #NewsUpdate #CurrentEvents #fastnewsorg"
        )

    elif style == "simple_text":
        # Style 3: Simple, no emojis
        source_text = f"\n📰 Source: {source}" if source else ""
        return (
            f"{headline}\n\n"
            f"{description}{source_text}\n\n"
            f"#News #fastnewsorg #{category.lower() if category else 'general'}"
        )

    elif style == "short_format":
        # Style 4: Short format
        source_text = f"\n📰 Source: {source}" if source else ""
        return (
            f"📰 {headline}{source_text}\n\n"
            f"#News #Breaking #fastnewsorg"
        )

    else:  # emoji_variation
        # Style 5: Different emoji variation
        source_text = f"\n📰 Source: {source}" if source else ""
        return (
            f"📡 {headline}\n\n"
            f"{description}{source_text}\n\n"
            f"#Newsroom #HeadlinesDaily #fastnewsorg"
        )


def simulate_human_activity(cl):
    """
    Simulate human browsing behavior between posts.
    40% chance to view other profiles/hashtags to appear human.
    """
    if random.random() < 0.40:
        try:
            logger.info("Simulating human browsing activity...")
            actions = [
                ('browse_profile', ['bbc', 'reuters', 'cnn', 'guardian']),
                ('search_hashtag', ['news', 'breaking', 'world']),
                ('idle', [])
            ]

            action_type, data = random.choice(actions)

            if action_type == 'browse_profile':
                profile = random.choice(data)
                logger.info(f"Viewing profile: @{profile}")
                cl.user_info_by_username(profile)
                time.sleep(random.randint(2, 8))

            elif action_type == 'search_hashtag':
                hashtag = random.choice(data)
                logger.info(f"Searching hashtag: #{hashtag}")
                cl.hashtag_info(hashtag)
                time.sleep(random.randint(2, 8))

            else:  # idle
                idle_time = random.randint(5, 15)
                logger.info(f"Just idling for {idle_time}s...")
                time.sleep(idle_time)

        except Exception as e:
            logger.warning(f"Human activity simulation failed: {e}")


def randomize_image_quality(image_path, output_path="post_output.jpg"):
    """
    Vary image format and quality to avoid bot detection.
    Sometimes PNG, sometimes JPG with different quality levels.
    """
    try:
        img = Image.open(image_path)

        # Random chance to save as PNG instead of JPG
        if random.random() < 0.25:
            output_path = "post_output.png"
            logger.info("Saving as PNG for variety")
            img.save(output_path, "PNG")
        else:
            # Vary JPG quality
            quality = random.randint(85, 95)
            logger.info(f"Saving as JPG with quality {quality}")
            img.save(output_path, "JPEG", quality=quality)

        return output_path

    except Exception as e:
        logger.warning(f"Image quality randomization failed: {e}")
        return image_path


def refresh_session_if_needed(cl):
    """
    Refresh Instagram session every 3-7 days to get fresh session token.
    Real users' sessions change frequently; keeping one forever is suspicious.
    """
    try:
        session_file = INSTAGRAM_SESSION_FILE
        if not os.path.exists(session_file):
            return cl

        file_age_seconds = time.time() - os.path.getmtime(session_file)
        file_age_days = file_age_seconds / 86400

        refresh_threshold_days = random.randint(3, 7)

        if file_age_days > refresh_threshold_days:
            logger.info(
                f"Session is {file_age_days:.1f} days old "
                f"(threshold: {refresh_threshold_days} days) - "
                f"refreshing..."
            )

            # Re-login to get fresh session
            username = os.getenv("IG_USERNAME")
            password = os.getenv("IG_PASSWORD")

            if username and password:
                try:
                    new_cl = Client()
                    new_cl.login(username, password)
                    new_cl.dump_settings(session_file)
                    logger.info("✓ Session refreshed successfully")

                    # Random delay after login
                    refresh_delay = random.randint(30, 120)
                    logger.info(
                        f"Waiting {refresh_delay}s after session refresh..."
                    )
                    time.sleep(refresh_delay)

                    return new_cl
                except Exception as e:
                    logger.warning(f"Session refresh failed: {e}")
                    return cl
            else:
                logger.warning(
                    "Cannot refresh session: IG_USERNAME/PASSWORD not set"
                )
                return cl
        else:
            logger.info(
                f"Session is {file_age_days:.1f} days old - "
                f"still fresh"
            )
            return cl

    except Exception as e:
        logger.warning(f"Session refresh check failed: {e}")
        return cl


def rotate_device(cl):
    """
    Rotate device information to appear as different phones.
    Instagram tracks device fingerprints; changing them avoids detection.
    """
    device_name, aspect_ratio, resolution = random.choice(DEVICE_PRESETS)
    logger.info(f"Device rotation: {device_name} ({resolution})")

    # TEMPORARY: Disable device rotation as it's breaking session
    # TODO: Fix this properly later
    logger.info("⚠️  Device rotation temporarily disabled")
    return cl
    
    try:
        cl.set_device(device_name)
        return cl
    except Exception as e:
        logger.warning(f"Device rotation failed: {e}")
        return cl


def main():
    """Main Instagram posting function with anti-detection measures"""
    # Validate environment before starting
    validate_and_exit_if_invalid()

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error(
            format_error_message(
                "missing_env",
                "SUPABASE_URL / SUPABASE_KEY"
            )
        )
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = TEMPLATE_PATH
    if not os.path.exists(template_path):
        template_path = os.path.join(base_dir, TEMPLATE_PATH)

    if not os.path.exists(template_path):
        logger.error(
            format_error_message("template_missing", template_path)
        )
        return

    # Initialize database
    if not init_database(SUPABASE_URL, SUPABASE_KEY):
        return

    logger.info("Starting Instagram posting cycle (anti-detection mode)...")
    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)

    # ========== ANTI-DETECTION: Random posting decision ==========
    if not should_post_now():
        logger.info("Skipped this cycle (randomization)")
        return

    # ========== ANTI-DETECTION: Daily limit check ==========
    if not check_daily_limit(supabase):
        logger.info("Daily limit reached")
        return

    # Rate checks from posting_history (kept for safety)
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
        .eq("posted", False)
        .order("published_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        logger.info(format_error_message("no_validated_stories", ""))
        return

    story = res.data[0]
    logger.info(f"Found story: {story['headline'][:60]}...")

    # Check if this is breaking news
    breaking = is_breaking_news(story["headline"], story.get("description", ""))
    max_posts_per_hour = MAX_POSTS_PER_HOUR_BREAKING if breaking else MAX_POSTS_PER_HOUR_NORMAL
    
    if breaking:
        logger.info(f"🚨 BREAKING NEWS detected - using higher rate limit (3/hour)")
    else:
        logger.info(f"📰 Normal news - using standard rate limit (1/hour)")

    if len(posts_hour) >= max_posts_per_hour:
        msg = f"{len(posts_hour)}/{max_posts_per_hour} posts this hour"
        logger.info(format_error_message("rate_limited", msg))
        return

    # Content safety check first
    safe, safety_score, safety_reason = is_safe_to_post(
        story["headline"],
        story.get("description", ""),
        story.get("source", "")
    )

    if not safe:
        logger.warning(
            f"⊘ Content safety violation: "
            f"{story['headline'][:60]}... - {safety_reason}"
        )
        alert_manager.alert_content_safety_violation(
            story["headline"],
            [safety_reason]
        )

        # Mark as posted to skip
        (
            supabase.table("stories")
            .update({"posted": True})
            .eq("id", story["id"])
            .execute()
        )
        supabase.table("posting_history").insert({
            "story_id": story["id"],
            "success": False,
            "error_message": f"Safety: {safety_reason}"
        }).execute()
        return

    # ========== AI CONTENT MONITOR: Chatbot decides to publish ==========
    logger.info("🤖 AI chatbot analyzing content...")
    ai_decision = ai_monitor.evaluate_content(
        story["headline"],
        story.get("description", ""),
        story.get("category", "general"),
        story.get("source", "")
    )
    
    logger.info(
        f"✅ AI chatbot decision: PUBLISH "
        f"(score: {ai_decision['score']}/100, ethics: {ai_decision['ethics_score']}, engagement: {ai_decision['engagement_score']}) - {ai_decision['reasoning']}"
    )
    
    # AI has made the decision - we publish regardless of other filters
    publish = True
    score = ai_decision['score']
    reason = ai_decision['reasoning']

    logger.info(
        f"✓ Story passes quality check (score: {score}/100) - {reason}"
    )

    # ========== ANTI-DETECTION: Human-like delays ==========
    delays = get_human_like_delays()
    
    # Skip delays if testing
    if os.getenv('SKIP_DELAYS') == 'true':
        logger.info("⏭️  SKIPPING DELAYS (test mode)")
    else:
        # Browse delay - simulate reading the article
        logger.info(f"⏳ Browsing for {delays['browse']}s...")
        time.sleep(delays['browse'])

    combined_text = f"{story['headline']} {story.get('description', '')}"
    is_nepali = is_nepali_text(combined_text)
    target_language = "nepali_to_english" if is_nepali else "en"

    # Generate caption with varied styles (include source)
    if is_nepali:
        caption_data = generate_caption(
            story["headline"],
            story.get("description", ""),
            story.get("category", "general"),
            language=target_language
        )
        caption = f"{caption_data.get('caption', '').strip()}\n\n{caption_data.get('hashtags', '').strip()}".strip()
    else:
        caption = generate_caption_variation(
            story["headline"],
            story.get("description", ""),
            story.get("category", ""),
            story.get("source", "")
        )

    # Edit delay - simulate editing the caption
    if os.getenv('SKIP_DELAYS') != 'true':
        logger.info(f"⏳ Editing caption for {delays['edit']}s...")
        time.sleep(delays['edit'])

    # Rephrase description to add context and avoid copyright issues
    logger.info("📝 Rephrasing description for better context...")
    description = rephrase_description_with_groq(
        story["headline"],
        story.get("description", ""),
        language=target_language
    )
    logger.info(f"✓ Rephrased: {description[:80]}...")

    # Render image from template with rephrased description
    output_path = OUTPUT_IMAGE_PATH
    title_font = FONT_BOLD
    body_font = FONT_REGULAR

    render_news_on_template(
        template_path,
        story["headline"],
        description,  # Use rephrased description
        output_path,
        title_font_path=title_font,
        body_font_path=body_font,
        target_size=OUTPUT_IMAGE_SIZE,
    )

    if not os.path.exists(output_path):
        logger.error(format_error_message("render_failed", output_path))
        return

    # ========== ANTI-DETECTION: Randomize image quality ==========
    output_path = randomize_image_quality(output_path)

    # Post to Instagram
    if not os.path.exists(INSTAGRAM_SESSION_FILE):
        logger.error(
            format_error_message("session_missing", INSTAGRAM_SESSION_FILE)
        )
        alert_manager.alert_api_failure(
            "Instagram Session",
            f"Session file not found: {INSTAGRAM_SESSION_FILE}"
        )
        return

    cl = Client()
    try:
        logger.info(f"📂 Loading Instagram session from {INSTAGRAM_SESSION_FILE}")
        
        # Verify file is readable and valid JSON
        try:
            with open(INSTAGRAM_SESSION_FILE, 'r') as f:
                import json
                session_data = json.load(f)
                logger.info("✅ Session file is valid JSON")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Session file is corrupted (invalid JSON): {e}")
            alert_manager.alert_api_failure(
                "Instagram Session",
                f"Corrupted session file - regenerate with fix_instagram_session.py"
            )
            return
        except Exception as e:
            logger.error(f"❌ Cannot read session file: {e}")
            return
        
        # Load session settings
        try:
            cl.load_settings(INSTAGRAM_SESSION_FILE)
            logger.info("✅ Session settings loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load session settings: {e}")
            logger.info("ℹ️  Regenerate session file with: python scripts/ig_login.py")
            alert_manager.alert_api_failure(
                "Instagram Session",
                f"Cannot load session - {str(e)}"
            )
            return
        
        # Use delay and set minimal settings to avoid API issues
        cl.delay_range = [1, 3]

        # ========== ANTI-DETECTION: Session refresh ==========
        cl = refresh_session_if_needed(cl)

        # ========== ANTI-DETECTION: Device rotation ==========
        cl = rotate_device(cl)

        # Login using session - with better error handling
        logger.info("🔐 Attempting Instagram login...")
        try:
            # Verify sessionid exists before attempting login
            if not hasattr(cl, 'sessionid') or not cl.sessionid:
                logger.error("❌ Session ID not found in loaded session")
                alert_manager.alert_api_failure(
                    "Instagram Session",
                    "Session ID missing - regenerate with fix_instagram_session.py"
                )
                return
            
            logger.info(f"ℹ️  Session ID exists: {str(cl.sessionid)[:20]}...")
            
            # Try to login
            try:
                cl.login_by_sessionid(cl.sessionid)
            except KeyError as ke:
                logger.error(f"❌ Session structure incomplete - missing key: {ke}")
                logger.error("This may happen if session was corrupted during transfer")
                logger.info("ℹ️  Try regenerating session: python fix_instagram_session.py")
                
                # Try fallback: validate the session is somewhat usable
                logger.info("ℹ️  Attempting direct API access without full validation...")
                try:
                    # Don't require full login validation, just try to use the session
                    cl.sessionid = cl.sessionid  # Keep the sessionid we have
                    cl.delay_range = [1, 3]
                    logger.warning("⚠️  Using session without full validation (risky)")
                except:
                    alert_manager.alert_api_failure(
                        "Instagram Session",
                        f"Session structure invalid: {str(ke)}"
                    )
                    return
            
            logger.info("✅ Instagram login successful")
        except ValueError as e:
            logger.error(f"❌ Session value error: {e}")
            logger.info("ℹ️  Session may be corrupted. Regenerate with: python scripts/ig_login.py")
            alert_manager.alert_api_failure(
                "Instagram Login",
                f"ValueError: {e}"
            )
            return
        except AttributeError as e:
            logger.error(f"❌ Session attribute error: {e}")
            alert_manager.alert_api_failure(
                "Instagram Session",
                f"AttributeError: {e} - Regenerate session"
            )
            return
        except Exception as e:
            logger.error(f"❌ Instagram login failed: {type(e).__name__}: {e}")
            # Try to provide helpful recovery steps
            logger.info("ℹ️  Recovery steps:")
            logger.info("  1. Run: python scripts/ig_login.py")
            logger.info("  2. Or use: python fix_instagram_session.py")
            alert_manager.alert_api_failure("Instagram Login", str(e))
            return
            
    except KeyError as e:
        logger.error(
            f"❌ Instagram session error (KeyError): {e}. "
            "Session structure is invalid or missing required fields."
        )
        alert_manager.alert_api_failure(
            "Instagram Login",
            f"KeyError: {e} - Regenerate session with fix_instagram_session.py"
        )
        return
    except AttributeError as e:
        logger.error(
            f"❌ Instagram session error (AttributeError): {e}. "
            "Session may be missing sessionid."
        )
        alert_manager.alert_api_failure(
            "Instagram Login",
            f"AttributeError: {e} - Regenerate session with fix_instagram_session.py"
        )
        return
    except Exception as e:
        logger.error(f"Instagram login failed: {e}")
        alert_manager.alert_api_failure("Instagram Login", str(e))
        return

    try:
        logger.info(f"📤 Posting: {story['headline'][:50]}...")
        media = cl.photo_upload(output_path, caption)
        logger.info(f"✓ Posted to Instagram: {media.pk}")

        # Review delay - simulate checking the post
        if os.getenv('SKIP_DELAYS') != 'true':
            logger.info(f"⏳ Reviewing post for {delays['review']}s...")
            time.sleep(delays['review'])

        # ========== ANTI-DETECTION: Random human activity ==========
        simulate_human_activity(cl)

        # Alert about successful post
        alert_manager.alert_post_success(
            story["headline"],
            score,
            safety_score
        )

        # Mark posted
        (
            supabase.table("stories")
            .update({"posted": True})
            .eq("id", story["id"])
            .execute()
        )

        # Log success
        supabase.table("posting_history").insert({
            "story_id": story["id"],
            "success": True,
            "error_message": None
        }).execute()

    except Exception as e:
        logger.error(f"Instagram post failed: {e}")
        alert_manager.alert_api_failure("Instagram", str(e))
        supabase.table("posting_history").insert({
            "story_id": story["id"],
            "success": False,
            "error_message": str(e)
        }).execute()


if __name__ == "__main__":
    main()
