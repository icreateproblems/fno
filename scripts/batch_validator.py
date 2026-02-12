"""
Background batch validator - runs separately from posting.
Validates stories in batches without blocking ingest.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import SUPABASE_URL, SUPABASE_KEY
from app.db_pool import get_supabase_client
from scripts.ai_content_monitor import AIContentMonitor
from app.logger import get_logger

logger = get_logger(__name__)

def batch_validate_stories(batch_size: int = 20):
    """
    Validate unvalidated stories in batches.
    Runs as separate cron job (every 5-10 minutes).
    """
    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
    ai_monitor = AIContentMonitor()
    # Get unvalidated stories
    stories = supabase.table("stories").select(
        "*"
    ).eq(
        "is_validated", False
    ).eq(
        "rejected", False
    ).limit(batch_size).execute().data
    if not stories:
        logger.info("No stories to validate")
        return
    logger.info(f"🤖 Validating {len(stories)} stories...")
    validated = 0
    rejected = 0
    for story in stories:
        try:
            decision = ai_monitor.evaluate_content(
                story['headline'],
                story.get('description', ''),
                story.get('category', 'general'),
                story.get('source', 'unknown')
            )
            should_publish = decision.get('should_publish') and decision.get('score', 0) >= 70
            supabase.table("stories").update({
                "is_validated": should_publish,
                "rejected": not should_publish,
                "ai_score": decision.get('score', 0)
            }).eq("id", story["id"]).execute()
            if should_publish:
                validated += 1
            else:
                rejected += 1
        except Exception as e:
            logger.error(f"Validation error: {e}")
            continue
    logger.info(f"✓ Validated: {validated}, Rejected: {rejected}")

if __name__ == "__main__":
    batch_validate_stories(batch_size=30)
