"""
Configuration management for News_Bot.
Centralized settings for easy tweaking.
Optimized for 2-3 posts/hour with native Nepali support.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# RSS SOURCES - Defined at module level for direct import
# ============================================================================
FREE_RSS_SOURCES = {
    # ============= NEPALI GENERAL NEWS =============
    "ekantipur": {
        "url": "https://ekantipur.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "online_khabar": {
        "url": "https://www.onlinekhabar.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "setopati": {
        "url": "https://setopati.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "nepali_times": {
        "url": "https://www.nepalitimes.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "naya_patrika": {
        "url": "https://nayapatrika.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "ratopati": {
        "url": "https://ratopati.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "republica": {
        "url": "https://www.myrepublica.com/feed",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
    "bbc_nepali": {
        "url": "https://bbc.com/nepali/rss.xml",
        "category": "general",
        "region": "Nepal",
        "timeout": 10,
    },
}

# Explicit exports for wildcard imports
__all__ = [
    'FREE_RSS_SOURCES',
    'Config',
    'SUPABASE_URL',
    'SUPABASE_KEY',
    'GROQ_API_KEY',
    'GROQ_EDITOR_API_KEY',
    'IMGBB_API_KEY',
    'INSTAGRAM_ACCESS_TOKEN',
    'INSTAGRAM_BUSINESS_ACCOUNT_ID',
    'INSTAGRAM_APP_ID',
    'INSTAGRAM_API_VERSION',
    'INSTAGRAM_SESSION_FILE',
    'TEMPLATE_PATH',
    'OUTPUT_IMAGE_PATH',
    'OUTPUT_IMAGE_SIZE',
    'TITLE_FONT_PATH',
    'BODY_FONT_PATH',
    'NEPALI_TITLE_FONT_PATH',
    'NEPALI_BODY_FONT_PATH',
    'MAX_POSTS_PER_HOUR_NORMAL',
    'MAX_POSTS_PER_HOUR_BREAKING',
    'MAX_POSTS_PER_DAY',
    'BREAKING_NEWS_KEYWORDS',
    'MIN_HEADLINE_LENGTH',
    'MAX_HEADLINE_LENGTH',
    'MIN_DESCRIPTION_LENGTH',
    'AI_VALIDATE_ON_INGEST',
    'AI_VALIDATE_MIN_SCORE',
    'CLEANUP_DAYS',
]

class Config:
    # ============================================================================
    # TARGET: 30-40 POSTS PER DAY (2-3 posts/hour)
    # ============================================================================
    DAILY_POST_TARGET_MIN = int(os.getenv('DAILY_POST_TARGET_MIN', '30'))
    DAILY_POST_TARGET_MAX = int(os.getenv('DAILY_POST_TARGET_MAX', '40'))
    POSTS_PER_HOUR_MIN = 2
    POSTS_PER_HOUR_MAX = 3
    DAILY_CAP = 25  # Instagram Graph API max - we'll stay under this
    
    # Nepal Peak Hours - Extended for more coverage (6AM-8PM)
    # 15 time slots × 2-3 posts = 30-45 posts/day
    PUBLISH_HOURS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    PUBLISH_MINUTE = 30
    
    # Content Categories for Diversity
    CONTENT_CATEGORIES = [
        'politics',      # Political news
        'economy',       # NEPSE, business, economy
        'sports',        # Cricket, football, golf, etc.
        'international', # World news
        'technology',    # Tech news
        'entertainment', # Movies, music, celebrations
        'society',       # Social issues, culture
        'general'        # Misc/general news
    ]
    
    # Category Distribution (ensure variety)
    CATEGORY_MIN_POSTS_PER_DAY = {
        'politics': 4,
        'economy': 3,
        'sports': 3,
        'international': 3,
        'technology': 2,
        'entertainment': 2,
        'society': 2,
        'general': 5
    }
    
    # ============================================================================
    # RELAXED FILTERS = 85% ACCEPT RATE
    # ============================================================================
    MIN_LENGTH_CHARS = 150
    MAX_LENGTH_CHARS = 1000
    MAX_AGE_HOURS = 168  # 7 days (was 48 for testing with older articles)
    MIN_COMPLETENESS = 70  # %
    
    # ============================================================================
    # API & DATABASE
    # ============================================================================
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # GROQ Editor API Key (Content validator/decider)
    GROQ_EDITOR_API_KEY = os.getenv("GROQ_EDITOR_API_KEY")
    GROQ_EDITOR_MODEL = "llama-3.3-70b-versatile"
    GROQ_EDITOR_TEMPERATURE = 0.3  # Lower for more consistent decisions
    
    # ============================================================================
    # INSTAGRAM VIA INSTAGRAM GRAPH API (Direct)
    # ============================================================================
    INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID")
    INSTAGRAM_API_VERSION = "v24.0"
    INSTAGRAM_ACCOUNTS = os.getenv('INSTAGRAM_ACCOUNTS', '').split(',')
    INSTAGRAM_SESSION_FILE = os.getenv("INSTAGRAM_SESSION_FILE", "instagram_session.json")
    GRAPH_TOKEN = os.getenv('GRAPH_LONG_TOKEN')  # Long-lived token
    
    # Image hosting for Graph API (requires public URLs)
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
    
    # ============================================================================
    # NEPALI RSS SOURCES FIRST
    # ============================================================================
    RSS_FEEDS = [
        'https://ekantipur.com/rss/news',
        'https://ekantipur.com/feed',
        'https://setopati.com/rss/news', 
        'https://setopati.com/feed',
        'https://onlinekhabar.com/feed',
        'https://www.onlinekhabar.com/feed',
        'https://ratopati.com/rss/news',
        'https://ratopati.com/feed',
        'https://bbc.com/nepali/rss.xml',
        'https://nayapatrika.com/feed',
        'https://www.nepalitimes.com/feed',
        'https://www.myrepublica.com/feed',
        # English fallback
        'https://feeds.bbci.co.uk/news/rss.xml',
        'https://rss.cnn.com/rss/edition.rss'
    ]
    
    # ============================================================================
    # RATE LIMITING (Legacy - kept for backward compatibility)
    # ============================================================================
    MAX_POSTS_PER_HOUR_NORMAL = POSTS_PER_HOUR_MAX
    MAX_POSTS_PER_HOUR_BREAKING = 4
    MAX_POSTS_PER_DAY = DAILY_CAP
    MIN_DELAY_MINUTES = 15
    
    # Breaking news detection keywords
    BREAKING_NEWS_KEYWORDS = [
        'breaking', 'urgent', 'alert', 'just in', 'developing',
        'तत्काल', 'ब्रेकिङ', 'जरुरी', 'अविलम्ब'
    ]
    
    # ============================================================================
    # STORY QUALITY FILTERS
    # ============================================================================
    MIN_HEADLINE_LENGTH = 10
    MAX_HEADLINE_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 30
    MIN_SOURCES_FOR_VALIDATION = 1  # Relaxed from 2
    
    # ============================================================================
    # AI VALIDATION (INGEST)
    # ============================================================================
    AI_VALIDATE_ON_INGEST = os.getenv("AI_VALIDATE_ON_INGEST", "true").lower() == "true"
    AI_VALIDATE_MIN_SCORE = int(os.getenv("AI_VALIDATE_MIN_SCORE", "50"))  # Relaxed from 55
    
    # ============================================================================
    # INSTAGRAM (via Facebook Graph API)
    # ============================================================================
    INSTAGRAM_MAX_RETRIES = 3
    INSTAGRAM_TIMEOUT = 30
    INSTAGRAM_POST_TYPE = "image"
    
    # ============================================================================
    # IMAGE RENDERING
    # ============================================================================
    TEMPLATE_PATH = "templates/breaking_template(1080).png"
    OUTPUT_IMAGE_PATH = "post_output.jpg"
    OUTPUT_IMAGE_SIZE = (1350, 1350)
    TITLE_FONT_PATH = "fonts/Inter-Bold.ttf"
    BODY_FONT_PATH = "fonts/Inter-Regular.ttf"
    NEPALI_TITLE_FONT_PATH = os.getenv("NEPALI_TITLE_FONT_PATH")
    NEPALI_BODY_FONT_PATH = os.getenv("NEPALI_BODY_FONT_PATH")
    
    # ============================================================================
    # GROQ AI
    # ============================================================================
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE = 0.4
    GROQ_MAX_TOKENS = 200
    GROQ_TIMEOUT = 15
    
    # ============================================================================
    # RETRY LOGIC
    # ============================================================================
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1
    MAX_BACKOFF = 32
    
    # ============================================================================
    # LOGGING
    # ============================================================================
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    LOG_FILE = "logs/news_bot.log"
    
    # ============================================================================
    # DATABASE CLEANUP
    # ============================================================================
    CLEANUP_DAYS = 30


# Module-level exports for backward compatibility
# Database
SUPABASE_URL = Config.SUPABASE_URL
SUPABASE_KEY = Config.SUPABASE_KEY

# API Keys
GROQ_API_KEY = Config.GROQ_API_KEY
GROQ_EDITOR_API_KEY = Config.GROQ_EDITOR_API_KEY
IMGBB_API_KEY = Config.IMGBB_API_KEY

# Instagram
INSTAGRAM_ACCESS_TOKEN = Config.INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ACCOUNT_ID = Config.INSTAGRAM_BUSINESS_ACCOUNT_ID
INSTAGRAM_APP_ID = Config.INSTAGRAM_APP_ID
INSTAGRAM_API_VERSION = Config.INSTAGRAM_API_VERSION
INSTAGRAM_SESSION_FILE = Config.INSTAGRAM_SESSION_FILE

# Templates & Fonts
TEMPLATE_PATH = Config.TEMPLATE_PATH
OUTPUT_IMAGE_PATH = Config.OUTPUT_IMAGE_PATH
OUTPUT_IMAGE_SIZE = Config.OUTPUT_IMAGE_SIZE
TITLE_FONT_PATH = Config.TITLE_FONT_PATH
BODY_FONT_PATH = Config.BODY_FONT_PATH
NEPALI_TITLE_FONT_PATH = Config.NEPALI_TITLE_FONT_PATH
NEPALI_BODY_FONT_PATH = Config.NEPALI_BODY_FONT_PATH

# Rate Limiting
MAX_POSTS_PER_HOUR_NORMAL = Config.MAX_POSTS_PER_HOUR_NORMAL
MAX_POSTS_PER_HOUR_BREAKING = Config.MAX_POSTS_PER_HOUR_BREAKING
MAX_POSTS_PER_DAY = Config.MAX_POSTS_PER_DAY
BREAKING_NEWS_KEYWORDS = Config.BREAKING_NEWS_KEYWORDS

# Story Validation
MIN_HEADLINE_LENGTH = Config.MIN_HEADLINE_LENGTH
MAX_HEADLINE_LENGTH = Config.MAX_HEADLINE_LENGTH
MIN_DESCRIPTION_LENGTH = Config.MIN_DESCRIPTION_LENGTH
AI_VALIDATE_ON_INGEST = Config.AI_VALIDATE_ON_INGEST
AI_VALIDATE_MIN_SCORE = Config.AI_VALIDATE_MIN_SCORE

# Database Cleanup
CLEANUP_DAYS = Config.CLEANUP_DAYS
