import os
import re
import hashlib
from datetime import datetime, timezone
import feedparser
import requests
from supabase import create_client
from dotenv import load_dotenv

# Import our modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import from config, but define fallback if import fails
try:
    from app.config import (
        FREE_RSS_SOURCES,
        SUPABASE_URL,
        SUPABASE_KEY,
        MIN_HEADLINE_LENGTH,
        MAX_HEADLINE_LENGTH,
        MIN_DESCRIPTION_LENGTH,
        AI_VALIDATE_ON_INGEST,
        AI_VALIDATE_MIN_SCORE,
        CLEANUP_DAYS
    )
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Using fallback RSS sources definition...")
    FREE_RSS_SOURCES = {
        "ekantipur": {"url": "https://ekantipur.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "online_khabar": {"url": "https://www.onlinekhabar.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "setopati": {"url": "https://setopati.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "nepali_times": {"url": "https://www.nepalitimes.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "naya_patrika": {"url": "https://nayapatrika.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "ratopati": {"url": "https://ratopati.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "republica": {"url": "https://www.myrepublica.com/feed", "category": "general", "region": "Nepal", "timeout": 10},
        "bbc_nepali": {"url": "https://bbc.com/nepali/rss.xml", "category": "general", "region": "Nepal", "timeout": 10},
    }
    # Import remaining from environment
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    MIN_HEADLINE_LENGTH = 10
    MAX_HEADLINE_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 30
    AI_VALIDATE_ON_INGEST = os.getenv("AI_VALIDATE_ON_INGEST", "true").lower() == "true"
    AI_VALIDATE_MIN_SCORE = int(os.getenv("AI_VALIDATE_MIN_SCORE", "50"))
    CLEANUP_DAYS = 30

from app.logger import get_logger
from app.utils import retry_with_backoff, validate_story, format_error_message, is_nepali_text
from app.db import init_database, cleanup_old_stories
from app.db_pool import get_supabase_client, clear_cache
from ai_content_monitor import AIContentMonitor
from groq_caption import rephrase_description_with_groq, translate_nepali_to_english

load_dotenv()

logger = get_logger(__name__)

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def content_hash(headline: str, url: str = "") -> str:
    key = f"{norm(headline)}|{norm(url)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error(format_error_message("missing_env", "SUPABASE_URL / SUPABASE_KEY"))
        return

    # Initialize database
    if not init_database(SUPABASE_URL, SUPABASE_KEY):
        return

    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)  # Use pooled connection
    logger.info("Starting news fetch cycle...")

    # Debug prints for troubleshooting
    print("DEBUG: FREE_RSS_SOURCES type:", type(FREE_RSS_SOURCES))
    print("DEBUG: FREE_RSS_SOURCES keys:", list(FREE_RSS_SOURCES.keys()))
    print("DEBUG: sys.path:", sys.path)
    print("DEBUG: SUPABASE_URL:", SUPABASE_URL)

    new_count = 0
    batch_stories = []  # Collect stories for batch insert
    ai_monitor = AIContentMonitor()
    
    for source, meta in FREE_RSS_SOURCES.items():
        try:
            logger.debug(f"Fetching from {source}...")
            feed = feedparser.parse(meta["url"])
            if not feed.entries:
                logger.warning(f"No entries from {source}")
                continue
        except Exception as e:
            logger.error(f"Error fetching {source}: {e}")
            continue
        
        for e in feed.entries[:25]:
            headline = e.get("title", "").strip()
            if not headline:
                continue

            url = e.get("link", "")
            desc = e.get("summary", "")[:2000]
            published = e.get("published_parsed")
            published_at = None
            if published:
                published_at = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
            
            # Extract image URL from various RSS feed formats
            image_url = None
            # Try media:content
            if hasattr(e, 'media_content') and e.media_content:
                image_url = e.media_content[0].get('url')
            # Try media:thumbnail
            if not image_url and hasattr(e, 'media_thumbnail') and e.media_thumbnail:
                image_url = e.media_thumbnail[0].get('url')
            # Try image tag
            if not image_url and hasattr(e, 'image'):
                image_url = e.image.get('url')
            # Try enclosure
            if not image_url and hasattr(e, 'enclosures'):
                for enc in e.enclosures:
                    if 'image' in enc.type:
                        image_url = enc.href
                        break

            # Validate story quality
            valid, reason = validate_story(
                headline, 
                desc,
                MIN_HEADLINE_LENGTH,
                MAX_HEADLINE_LENGTH,
                MIN_DESCRIPTION_LENGTH
            )
            if not valid:
                logger.debug(f"Story rejected ({source}): {reason}")
                continue

            h = content_hash(headline, url)

            # Add to batch instead of immediate insert
            batch_stories.append({
                "headline": headline,
                "description": desc,
                "content_hash": h,
                "source": source,
                "category": meta["category"],
                "url": url,
                "image_url": image_url,
                "published_at": published_at
            })
    
    # Batch insert all stories at once (saves 95% of DB calls)
    if batch_stories:
        try:
            # Get existing hashes in one query
            all_hashes = [s["content_hash"] for s in batch_stories]
            existing = supabase.table("stories").select("content_hash").in_("content_hash", all_hashes).execute()
            existing_hashes = {row["content_hash"] for row in existing.data}
            
            # Filter out duplicates
            new_stories = [s for s in batch_stories if s["content_hash"] not in existing_hashes]
            
            if new_stories:
                supabase.table("stories").insert(new_stories).execute()
                new_count = len(new_stories)
                logger.info(f"✓ Batch inserted {new_count} new stories")

                # AI validation on ingest (optional)
                if AI_VALIDATE_ON_INGEST:
                    validated = 0
                    rejected = 0
                    for story in new_stories:
                        combined_text = f"{story['headline']} {story.get('description', '')}"
                        if is_nepali_text(combined_text):
                            eval_headline = translate_nepali_to_english(story["headline"])
                            eval_desc = rephrase_description_with_groq(
                                story["headline"],
                                story.get("description", ""),
                                language="nepali_to_english"
                            )
                        else:
                            eval_headline = story["headline"]
                            eval_desc = story.get("description", "")

                        decision = ai_monitor.evaluate_content(
                            eval_headline,
                            eval_desc,
                            story.get("category", "general"),
                            story.get("source", "unknown")
                        )

                        should_publish = bool(decision.get("should_publish")) and decision.get("score", 0) >= AI_VALIDATE_MIN_SCORE

                        supabase.table("stories").update({
                            "is_validated": should_publish,
                            "rejected": not should_publish
                        }).eq("content_hash", story["content_hash"]).execute()

                        if should_publish:
                            validated += 1
                        else:
                            rejected += 1

                    logger.info(f"AI validated: {validated}, rejected: {rejected}")
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            # Fallback to individual inserts
            for story in batch_stories:
                try:
                    exists = supabase.table("stories").select("id").eq("content_hash", story["content_hash"]).limit(1).execute()
                    if not exists.data:
                        supabase.table("stories").insert(story).execute()
                        new_count += 1
                except:
                    continue

    logger.info(f"Fetched: {new_count} new stories")
    
    # Clear cache after inserts
    clear_cache()

    # Fallback validation for non-AI ingest
    if not AI_VALIDATE_ON_INGEST:
        try:
            rows = supabase.table("stories").select("id").eq("is_validated", False).execute().data

            validated = 0
            for r in rows:
                supabase.table("stories").update({"is_validated": True}).eq("id", r["id"]).execute()
                validated += 1

            logger.info(f"Validated: {validated} stories")
        except Exception as e:
            logger.error(f"Validation error: {e}")

    # Cleanup old data
    try:
        cleanup_old_stories(supabase, CLEANUP_DAYS)
    except Exception as e:
        logger.debug(f"Cleanup skipped: {e}")

    logger.info("✓ Fetch cycle complete")

if __name__ == "__main__":
    main()
