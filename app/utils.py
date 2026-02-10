"""
Utility functions: retry logic, validators, helpers.
"""
import time
import functools
from typing import Callable, Any

# Prefer package import; fall back for legacy callers
try:
    from app.logger import get_logger
except ModuleNotFoundError:  # pragma: no cover
    from logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# RETRY LOGIC WITH EXPONENTIAL BACKOFF
# ============================================================================

def retry_with_backoff(max_retries: int = 3, initial_backoff: float = 1, max_backoff: float = 32):
    """
    Decorator for automatic retry with exponential backoff.
    
    Usage:
        @retry_with_backoff(max_retries=3)
        def flaky_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            backoff = initial_backoff
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt+1}/{max_retries+1}): {e}"
                        )
                        logger.debug(f"Backing off for {backoff}s...")
                        time.sleep(backoff)
                        backoff = min(backoff * 2, max_backoff)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries+1} attempts: {e}"
                        )
            
            raise last_exception
        return wrapper
    return decorator

# ============================================================================
# STORY QUALITY VALIDATORS
# ============================================================================

def is_valid_headline(headline: str, min_len: int = 10, max_len: int = 200) -> tuple[bool, str]:
    """
    Validate headline quality.
    Returns (is_valid, reason)
    """
    if not headline:
        return False, "Empty headline"
    
    headline = headline.strip()
    
    if len(headline) < min_len:
        return False, f"Headline too short ({len(headline)} < {min_len} chars)"
    
    if len(headline) > max_len:
        return False, f"Headline too long ({len(headline)} > {max_len} chars)"
    
    # Reject all-caps headlines (usually clickbait)
    if headline.isupper() and len(headline) > 20:
        return False, "All-caps headline (likely clickbait)"
    
    # Reject excessive punctuation (!!!, ???)
    if headline.count('!') > 2 or headline.count('?') > 2:
        return False, "Excessive punctuation (likely clickbait)"
    
    return True, "OK"

def is_valid_description(description: str, min_len: int = 30) -> tuple[bool, str]:
    """
    Validate description quality.
    Returns (is_valid, reason)
    """
    if not description:
        return False, "Empty description"
    
    description = description.strip()
    
    if len(description) < min_len:
        return False, f"Description too short ({len(description)} < {min_len} chars)"
    
    return True, "OK"

def validate_story(headline: str, description: str, min_headline_len: int = 10, 
                   max_headline_len: int = 200, min_desc_len: int = 30) -> tuple[bool, str]:
    """
    Comprehensive story validation.
    Returns (is_valid, reason)
    """
    valid, reason = is_valid_headline(headline, min_headline_len, max_headline_len)
    if not valid:
        return False, f"Headline: {reason}"
    
    valid, reason = is_valid_description(description, min_desc_len)
    if not valid:
        return False, f"Description: {reason}"
    
    return True, "OK"

# ============================================================================
# ERROR MESSAGES WITH ACTIONABLE ADVICE
# ============================================================================

def format_error_message(error_type: str, details: str) -> str:
    """Format error messages with helpful advice."""
    
    advice = {
        "missing_env": (
            "❌ Missing environment variable\n"
            "💡 Fix: Add to .env file:\n"
            f"   {details}=your_value_here"
        ),
        "invalid_api_key": (
            "❌ Invalid API key\n"
            "💡 Fix: Check .env file, ensure credentials are correct\n"
            f"   Error: {details}"
        ),
        "instagram_session_expired": (
            "❌ Instagram session expired\n"
            "💡 Fix: Run 'python scripts/ig_login.py' to create new session"
        ),
        "template_missing": (
            "❌ Template image not found\n"
            "💡 Fix: Create templates/breaking_template.jpg\n"
            f"   Expected: {details}"
        ),
        "rate_limited": (
            "⏸️  Rate limited\n"
            "💡 Info: Too many posts recently, waiting for quota reset\n"
            f"   Details: {details}"
        ),
        "no_validated_stories": (
            "ℹ️  No new stories to post\n"
            "💡 Info: Need stories from ≥2 sources to validate\n"
            "   Waiting for next news cycle..."
        ),
        "network_error": (
            "❌ Network error\n"
            "💡 Fix: Check internet connection or API status\n"
            f"   Error: {details}"
        ),
        "database_error": (
            "❌ Database error\n"
            "💡 Fix: Check Supabase connection\n"
            f"   Error: {details}"
        ),
    }
    
    return advice.get(error_type, f"❌ {error_type}: {details}")

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def validate_db_connection(supabase_url: str, supabase_key: str) -> tuple[bool, str]:
    """Validate Supabase connection early."""
    if not supabase_url or not supabase_key:
        return False, "Missing SUPABASE_URL or SUPABASE_KEY"
    
    if not supabase_url.startswith("https://"):
        return False, "Invalid SUPABASE_URL (should be HTTPS)"
    
    if len(supabase_key) < 20:
        return False, "Invalid SUPABASE_KEY (too short)"
    
    return True, "OK"

def validate_groq_key(groq_key: str) -> tuple[bool, str]:
    """Validate Groq API key format."""
    if not groq_key:
        return False, "Missing GROQ_API_KEY"
    
    if not groq_key.startswith("gsk_"):
        return False, "Invalid GROQ_API_KEY format (should start with 'gsk_')"
    
    return True, "OK"

# ============================================================================
# LANGUAGE DETECTION (LIGHTWEIGHT)
# ============================================================================

def is_nepali_text(text: str, min_ratio: float = 0.08) -> bool:
    """
    Detect Nepali/Devanagari script using Unicode range U+0900–U+097F.
    min_ratio is the minimum proportion of Nepali characters.
    """
    if not text:
        return False

    total = 0
    nepali = 0
    for ch in text:
        if ch.isspace():
            continue
        total += 1
        if "\u0900" <= ch <= "\u097F":
            nepali += 1

    if total == 0:
        return False
    return (nepali / total) >= min_ratio
