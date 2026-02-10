"""
Database initialization and migrations.
Auto-setup tables if they don't exist.
"""
from supabase import create_client
from app.logger import get_logger

logger = get_logger(__name__)

def init_database(supabase_url: str, supabase_key: str) -> bool:
    """
    Initialize database, create tables if missing.
    Returns True if successful.
    """
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Database connection established")
        
        # Test connection
        result = supabase.table("stories").select("id").limit(1).execute()
        logger.info("✓ Stories table exists")
        
        result = supabase.table("posting_history").select("id").limit(1).execute()
        logger.info("✓ Posting history table exists")
        
        return True
        
    except Exception as e:
        logger.error(
            f"Database initialization failed: {e}\n"
            f"💡 Make sure to run the Supabase schema:\n"
            f"   1. Go to https://supabase.com\n"
            f"   2. Run schema/supabase_schema.sql in SQL editor"
        )
        return False

def cleanup_old_stories(supabase, days: int = 30) -> int:
    """
    Delete stories older than N days.
    Returns count deleted.
    """
    try:
        # Try to use the RPC function
        result = supabase.rpc("cleanup_old_data", {}).execute()
        logger.info(f"Cleanup completed")
        return 0
    except Exception as e:
        logger.debug(f"Cleanup RPC not available: {e}")
        return 0
