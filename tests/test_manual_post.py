"""
Manual test script to post to Instagram (bypasses random checks)
Use this for testing only - not for production
"""
import os
import sys

# Set environment to bypass random checks
os.environ['FORCE_POST'] = 'true'
# Skip human-like delays for testing
os.environ['SKIP_DELAYS'] = 'true'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.post_instagram import main, should_post_now

# Monkey patch should_post_now to always return True
original_should_post_now = should_post_now

def force_post_now():
    """Override to always post for testing"""
    print("🔧 TEST MODE: Bypassing random checks...")
    return True

# Replace the function
import scripts.post_instagram as post_module
post_module.should_post_now = force_post_now

# Run main
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 MANUAL TEST POST - BYPASSING RANDOM CHECKS & DELAYS")
    print("=" * 70)
    main()
