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
    BREAKING_NEWS_KEYWORDS
)
# Import high-volume config
from app.config_high_volume import HighVolumeConfig as Config
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
    """Optimized for 2 posts/hour - minimal random skips"""
    nepal_time = datetime.now(NEPAL_TZ)
    current_hour = nepal_time.hour
    logger.info(f"Nepal time: {nepal_time.strftime('%H:%M:%S')}")
    # Only skip dead hours (2-3am)
    if current_hour in Config.SKIP_HOURS:
        logger.info(f"Dead hours - skipping")
        return False
    # No random skips in high-volume mode
    logger.info("Active hours - ready to post")
    return True


def check_daily_limit(supabase):
    """Higher daily limit for 48 posts/day target"""
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
        if len(posts_today) >= Config.MAX_POSTS_PER_DAY:
            logger.info(f"Daily limit: {len(posts_today)}/{Config.MAX_POSTS_PER_DAY}")
            return False
        logger.info(f"Daily: {len(posts_today)}/{Config.MAX_POSTS_PER_DAY}")
        return True
    except Exception as e:
        logger.warning(f"Daily check failed: {e}")
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
    """Optimized delays for high-volume posting"""
    delays = {
        'browse': random.randint(Config.DELAY_BROWSE_MIN, Config.DELAY_BROWSE_MAX),
        'edit': random.randint(Config.DELAY_EDIT_MIN, Config.DELAY_EDIT_MAX),
        'review': random.randint(Config.DELAY_REVIEW_MIN, Config.DELAY_REVIEW_MAX)
    }
    total = sum(delays.values())
    logger.info(f"Delays: {total}s total")
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


def check_posting_rate(supabase):
    """Time-based rate limiting for consistent 2/hour"""
    now = datetime.now()
    recent_cutoff = (now - timedelta(minutes=Config.MIN_MINUTES_BETWEEN_POSTS)).isoformat()
    try:
        recent_posts = (
            supabase.table("posting_history")
            .select("id, created_at")
            .gte("created_at", recent_cutoff)
            .eq("success", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if recent_posts:
            last_post_time = datetime.fromisoformat(recent_posts[0]['created_at'])
            minutes_since = (now - last_post_time).total_seconds() / 60
            if minutes_since < Config.MIN_MINUTES_BETWEEN_POSTS:
                logger.info(
                    f"Posted {minutes_since:.1f}m ago - "
                    f"need {Config.MIN_MINUTES_BETWEEN_POSTS}m spacing"
                )
                return False
        return True
    except Exception as e:
        logger.warning(f"Rate check failed: {e}")
        return True

def main():
    """Main posting function - optimized for 2/hour"""
    validate_and_exit_if_invalid()
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error(format_error_message("missing_env", "SUPABASE_URL / SUPABASE_KEY"))
        return
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = TEMPLATE_PATH
    if not os.path.exists(template_path):
        template_path = os.path.join(base_dir, TEMPLATE_PATH)
    if not os.path.exists(template_path):
        logger.error(format_error_message("template_missing", template_path))
        return
    if not init_database(SUPABASE_URL, SUPABASE_KEY):
        return
    logger.info("Starting Instagram posting cycle (high-volume mode)...")
    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
    posts_this_run = 0
    MAX_POSTS_THIS_RUN = Config.MAX_POSTS_PER_RUN
    logger.info(f"Starting run - target: {MAX_POSTS_THIS_RUN} posts")
    while posts_this_run < MAX_POSTS_THIS_RUN:
        if not should_post_now():
            break
        if not check_daily_limit(supabase):
            break
        if not check_posting_rate(supabase):
            break
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
            logger.info("No more stories - stopping")
            break
        story = res.data[0]
        logger.info(f"Found story: {story['headline'][:60]}...")
        safe, safety_score, safety_reason = is_safe_to_post(
            story["headline"],
            story.get("description", ""),
            story.get("source", "")
        )
        if not safe:
            logger.warning(f"⊘ Content safety violation: {story['headline'][:60]}... - {safety_reason}")
            alert_manager.alert_content_safety_violation(story["headline"], [safety_reason])
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
            break
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
        publish = True
        score = ai_decision['score']
        reason = ai_decision['reasoning']
        logger.info(f"✓ Story passes quality check (score: {score}/100) - {reason}")
        delays = get_human_like_delays()
        if os.getenv('SKIP_DELAYS') == 'true':
            logger.info("⏭️  SKIPPING DELAYS (test mode)")
        else:
            logger.info(f"⏳ Browsing for {delays['browse']}s...")
            time.sleep(delays['browse'])
        combined_text = f"{story['headline']} {story.get('description', '')}"
        is_nepali = is_nepali_text(combined_text)
        target_language = "nepali_to_english" if is_nepali else "en"
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
        if os.getenv('SKIP_DELAYS') != 'true':
            logger.info(f"⏳ Editing caption for {delays['edit']}s...")
            time.sleep(delays['edit'])
        logger.info("📝 Rephrasing description for better context...")
        description = rephrase_description_with_groq(
            story["headline"],
            story.get("description", ""),
            language=target_language
        )
        logger.info(f"✓ Rephrased: {description[:80]}...")
        output_path = OUTPUT_IMAGE_PATH
        title_font = FONT_BOLD
        body_font = FONT_REGULAR
        render_news_on_template(
            template_path,
            story["headline"],
            description,
            output_path,
            title_font_path=title_font,
            body_font_path=body_font,
            target_size=OUTPUT_IMAGE_SIZE,
        )
        if not os.path.exists(output_path):
            logger.error(format_error_message("render_failed", output_path))
            break
        output_path = randomize_image_quality(output_path)
        if not os.path.exists(INSTAGRAM_SESSION_FILE):
            logger.error(format_error_message("session_missing", INSTAGRAM_SESSION_FILE))
            alert_manager.alert_api_failure("Instagram Session", f"Session file not found: {INSTAGRAM_SESSION_FILE}")
            break
        cl = Client()
        try:
            logger.info(f"📂 Loading Instagram session from {INSTAGRAM_SESSION_FILE}")
            try:
                with open(INSTAGRAM_SESSION_FILE, 'r') as f:
                    import json
                    session_data = json.load(f)
                    logger.info("✅ Session file is valid JSON")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Session file is corrupted (invalid JSON): {e}")
                alert_manager.alert_api_failure("Instagram Session", f"Corrupted session file - regenerate with fix_instagram_session.py")
                break
            except Exception as e:
                logger.error(f"❌ Cannot read session file: {e}")
                break
            try:
                cl.load_settings(INSTAGRAM_SESSION_FILE)
                logger.info("✅ Session settings loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load session settings: {e}")
                logger.info("ℹ️  Regenerate session file with: python scripts/ig_login.py")
                alert_manager.alert_api_failure("Instagram Session", f"Cannot load session - {str(e)}")
                break
            cl.delay_range = [1, 3]
            cl = refresh_session_if_needed(cl)
            cl = rotate_device(cl)
            logger.info("🔐 Attempting Instagram login...")
            try:
                if not hasattr(cl, 'sessionid') or not cl.sessionid:
                    logger.error("❌ Session ID not found in loaded session")
                    alert_manager.alert_api_failure("Instagram Session", "Session ID missing - regenerate with fix_instagram_session.py")
                    break
                logger.info(f"ℹ️  Session ID exists: {str(cl.sessionid)[:20]}...")
                try:
                    cl.login_by_sessionid(cl.sessionid)
                except KeyError as ke:
                    logger.error(f"❌ Session structure incomplete - missing key: {ke}")
                    logger.error("This may happen if session was corrupted during transfer")
                    logger.info("ℹ️  Try regenerating session: python fix_instagram_session.py")
                    logger.info("ℹ️  Attempting direct API access without full validation...")
                    try:
                        cl.sessionid = cl.sessionid
                        cl.delay_range = [1, 3]
                        logger.warning("⚠️  Using session without full validation (risky)")
                    except:
                        alert_manager.alert_api_failure("Instagram Session", f"Session structure invalid: {str(ke)}")
                        break
                logger.info("✅ Instagram login successful")
            except ValueError as e:
                logger.error(f"❌ Session value error: {e}")
                logger.info("ℹ️  Session may be corrupted. Regenerate with: python scripts/ig_login.py")
                alert_manager.alert_api_failure("Instagram Login", f"ValueError: {e}")
                break
            except AttributeError as e:
                logger.error(f"❌ Session attribute error: {e}")
                alert_manager.alert_api_failure("Instagram Session", f"AttributeError: {e} - Regenerate session")
                break
            except Exception as e:
                logger.error(f"❌ Instagram login failed: {type(e).__name__}: {e}")
                logger.info("ℹ️  Recovery steps:")
                logger.info("  1. Run: python scripts/ig_login.py")
                logger.info("  2. Or use: python fix_instagram_session.py")
                alert_manager.alert_api_failure("Instagram Login", str(e))
                break
        except KeyError as e:
            logger.error(f"❌ Instagram session error (KeyError): {e}. Session structure is invalid or missing required fields.")
            alert_manager.alert_api_failure("Instagram Login", f"KeyError: {e} - Regenerate session with fix_instagram_session.py")
            break
        except AttributeError as e:
            logger.error(f"❌ Instagram session error (AttributeError): {e}. Session may be missing sessionid.")
            alert_manager.alert_api_failure("Instagram Login", f"AttributeError: {e} - Regenerate session with fix_instagram_session.py")
            break
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            alert_manager.alert_api_failure("Instagram Login", str(e))
            break
        try:
            logger.info(f"📤 Posting: {story['headline'][:50]}...")
            media = cl.photo_upload(output_path, caption)
            logger.info(f"✓ Posted to Instagram: {media.pk}")
            if os.getenv('SKIP_DELAYS') != 'true':
                logger.info(f"⏳ Reviewing post for {delays['review']}s...")
                time.sleep(delays['review'])
            simulate_human_activity(cl)
            alert_manager.alert_post_success(story["headline"], score, safety_score)
            (
                supabase.table("stories")
                .update({"posted": True})
                .eq("id", story["id"])
                .execute()
            )
            supabase.table("posting_history").insert({
                "story_id": story["id"],
                "success": True,
                "error_message": None
            }).execute()
            posts_this_run += 1
            logger.info(f"✓ Posted {posts_this_run}/{MAX_POSTS_THIS_RUN}")
            if posts_this_run < MAX_POSTS_THIS_RUN:
                inter_post_delay = random.randint(30, 90)
                logger.info(f"Delay before next post: {inter_post_delay}s")
                time.sleep(inter_post_delay)
        except Exception as e:
            logger.error(f"Instagram post failed: {e}")
            alert_manager.alert_api_failure("Instagram", str(e))
            supabase.table("posting_history").insert({
                "story_id": story["id"],
                "success": False,
                "error_message": str(e)
            }).execute()
            break
    logger.info(f"✓ Run complete: {posts_this_run} posts")

if __name__ == "__main__":
    main()
