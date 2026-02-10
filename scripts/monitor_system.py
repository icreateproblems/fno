# Monitoring script to run periodically and send alerts if needed

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app.health_check import HealthCheck
from app.db_pool import get_supabase_client
from app.alerts import alert_manager
from app.error_recovery import error_tracker
from app.logger import get_logger

logger = get_logger(__name__)


def check_system_health():
    """Run health check and alert if issues found."""
    health = HealthCheck()
    health.run_all_checks()
    
    status, failures = health.get_overall_status()
    
    if status in ["DEGRADED", "CRITICAL"]:
        logger.error(f"System status: {status}")
        alert_manager.alert_health_check_failed(failures)
        return False
    
    logger.info("✅ System healthy")
    return True


def check_posting_activity():
    """Check if bot has posted recently."""
    try:
        supabase = get_supabase_client()
        cutoff = (datetime.utcnow() - timedelta(hours=3)).isoformat()
        
        result = supabase.table("posting_history")\
            .select("id")\
            .gte("posted_at", cutoff)\
            .eq("success", True)\
            .execute()
        
        post_count = len(result.data) if result.data else 0
        
        if post_count == 0:
            logger.warning("No posts in last 3 hours")
            alert_manager.alert_posting_stopped(3)
            return False
        
        logger.info(f"✅ {post_count} posts in last 3 hours")
        return True
    
    except Exception as e:
        logger.error(f"Error checking posting activity: {str(e)}")
        return False


def check_error_rate():
    """Check if error rate is acceptable."""
    error_rate = error_tracker.get_error_rate(minutes=10)
    threshold = 1.0  # 1 error per minute
    
    if error_rate > threshold:
        logger.warning(f"High error rate: {error_rate:.2f}/min")
        alert_manager.alert_high_error_rate(error_rate, threshold)
        return False
    
    logger.info(f"✅ Error rate normal: {error_rate:.2f}/min")
    return True


def check_storage():
    """Check database storage usage."""
    try:
        supabase = get_supabase_client()
        
        story_result = supabase.table("stories").select("id", count="exact").execute()
        story_count = story_result.count if hasattr(story_result, 'count') else 0
        
        post_result = supabase.table("posting_history").select("id", count="exact").execute()
        post_count = post_result.count if hasattr(post_result, 'count') else 0
        
        estimated_mb = (story_count * 2 + post_count * 0.5) / 1024
        limit_mb = 500  # Supabase free tier
        
        if estimated_mb > 400:
            logger.warning(f"High storage usage: {estimated_mb:.1f}MB")
            alert_manager.alert_storage_warning(estimated_mb, limit_mb)
            return False
        
        logger.info(f"✅ Storage: {estimated_mb:.1f}MB / {limit_mb}MB")
        return True
    
    except Exception as e:
        logger.error(f"Error checking storage: {str(e)}")
        return False


def main():
    """Run all monitoring checks."""
    logger.info("="*60)
    logger.info("Starting monitoring checks...")
    logger.info("="*60)
    
    checks = [
        ("System Health", check_system_health),
        ("Posting Activity", check_posting_activity),
        ("Error Rate", check_error_rate),
        ("Storage Usage", check_storage),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\nRunning: {check_name}")
        results[check_name] = check_func()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("MONITORING SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for check_name, result in results.items():
        status_icon = "✅" if result else "❌"
        logger.info(f"{status_icon} {check_name}: {'PASS' if result else 'FAIL'}")
    
    logger.info(f"\nTotal: {passed}/{total} checks passed")
    logger.info("="*60)
    
    # Exit with appropriate code
    if passed == total:
        sys.exit(0)
    elif passed >= total * 0.75:
        sys.exit(1)  # Degraded
    else:
        sys.exit(2)  # Critical


if __name__ == "__main__":
    main()
