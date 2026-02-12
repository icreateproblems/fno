"""
High-volume configuration for 2 posts/hour target.
Optimized for throughput while maintaining quality.
"""
import os
from app.config import Config

class HighVolumeConfig(Config):
    """Configuration optimized for 48 posts/day"""
    # HIGH-VOLUME TARGETS
    POSTS_PER_HOUR_TARGET = 2
    POSTS_PER_DAY_TARGET = 48

    # RATE LIMITS (INCREASED)
    MAX_POSTS_PER_HOUR_NORMAL = 4      # Increased from 3
    MAX_POSTS_PER_HOUR_BREAKING = 6    # Increased from 4
    MAX_POSTS_PER_DAY = 50             # Increased from 20
    MAX_POSTS_PER_RUN = 2              # Allow 2 per CircleCI run

    # TIMING OPTIMIZATION
    MIN_MINUTES_BETWEEN_POSTS = 25     # 25 min spacing = 2.4 posts/hour

    # Disable random skips in production
    ENABLE_RANDOM_SKIP = False

    # Reduced delays for throughput
    DELAY_BROWSE_MIN = 5      # Reduced from 30
    DELAY_BROWSE_MAX = 15     # Reduced from 180
    DELAY_EDIT_MIN = 3        # Reduced from 15
    DELAY_EDIT_MAX = 8        # Reduced from 90
    DELAY_REVIEW_MIN = 2      # Reduced from 10
    DELAY_REVIEW_MAX = 5      # Reduced from 60

    # CONTENT SUPPLY (INCREASED)
    RSS_ENTRIES_PER_SOURCE = 50        # Increased from 25

    # Disable slow on-ingest validation
    AI_VALIDATE_ON_INGEST = False

    # Run batch validation separately
    BATCH_VALIDATION_ENABLED = True
    BATCH_VALIDATION_SIZE = 30

    # QUALITY THRESHOLDS (MAINTAINED)
    AI_VALIDATE_MIN_SCORE = 70         # Keep high quality bar

    # ACTIVE HOURS (EXPANDED)
    SKIP_HOURS = [2, 3]  # Only skip 2-3am

    # FEATURE FLAGS
    SKIP_DELAYS_IN_PRODUCTION = os.getenv('SKIP_DELAYS', 'false').lower() == 'true'
