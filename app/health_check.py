"""
Health check and monitoring system for News Bot.
Validates all critical systems and provides detailed status reports.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import requests
from app.logger import get_logger
from app.config import SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY

logger = get_logger(__name__)


class HealthCheck:
    """Comprehensive health check for all system components."""
    
    def __init__(self):
        self.checks: List[Tuple[str, callable]] = [
            ("Environment Variables", self.check_env_vars),
            ("Supabase Connection", self.check_supabase),
            ("GROQ API", self.check_groq),
            ("Database Schema", self.check_database_schema),
            ("Recent Posts", self.check_recent_activity),
            ("Error Rate", self.check_error_rate),
            ("Storage Usage", self.check_storage),
        ]
        self.results: Dict[str, Dict] = {}
    
    def check_env_vars(self) -> Tuple[bool, str]:
        """Validate all required environment variables."""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "GROQ_API_KEY",
            "IG_USERNAME",
            "IG_PASSWORD",
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            return False, f"Missing variables: {', '.join(missing)}"
        
        # Validate format
        if not SUPABASE_URL.startswith("https://"):
            return False, "SUPABASE_URL must start with https://"
        
        if len(SUPABASE_KEY) < 20:
            return False, "SUPABASE_KEY appears invalid (too short)"
        
        if len(GROQ_API_KEY) < 20:
            return False, "GROQ_API_KEY appears invalid (too short)"
        
        return True, "All environment variables valid"
    
    def check_supabase(self) -> Tuple[bool, str]:
        """Check Supabase connectivity and authentication."""
        try:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Supabase connected successfully"
            else:
                return False, f"Supabase returned status {response.status_code}"
        
        except requests.exceptions.Timeout:
            return False, "Supabase connection timeout"
        except Exception as e:
            return False, f"Supabase error: {str(e)}"
    
    def check_groq(self) -> Tuple[bool, str]:
        """Check GROQ API connectivity."""
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Simple test request
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                },
                timeout=15
            )
            
            if response.status_code in [200, 429]:  # 429 = rate limit (but API key works)
                return True, "GROQ API accessible"
            else:
                return False, f"GROQ returned status {response.status_code}"
        
        except Exception as e:
            return False, f"GROQ error: {str(e)}"
    
    def check_database_schema(self) -> Tuple[bool, str]:
        """Verify database tables exist."""
        try:
            from app.db_pool import get_supabase_client
            supabase = get_supabase_client()
            
            # Check required tables
            tables = ["stories", "posting_history"]
            
            for table in tables:
                result = supabase.table(table).select("id").limit(1).execute()
                if not hasattr(result, 'data'):
                    return False, f"Table '{table}' not accessible"
            
            return True, "Database schema valid"
        
        except Exception as e:
            return False, f"Schema error: {str(e)}"
    
    def check_recent_activity(self) -> Tuple[bool, str]:
        """Check if bot has posted recently."""
        try:
            from app.db_pool import get_supabase_client
            supabase = get_supabase_client()
            
            cutoff = (datetime.utcnow() - timedelta(hours=2)).isoformat()
            
            result = supabase.table("posting_history")\
                .select("id")\
                .gte("posted_at", cutoff)\
                .execute()
            
            count = len(result.data) if result.data else 0
            
            if count > 0:
                return True, f"{count} posts in last 2 hours"
            else:
                return False, "No posts in last 2 hours (possible issue)"
        
        except Exception as e:
            return False, f"Activity check error: {str(e)}"
    
    def check_error_rate(self) -> Tuple[bool, str]:
        """Check error rate in recent posts."""
        try:
            from app.db_pool import get_supabase_client
            supabase = get_supabase_client()
            
            cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Get total stories
            total = supabase.table("stories")\
                .select("id", count="exact")\
                .gte("created_at", cutoff)\
                .execute()
            
            total_count = total.count if hasattr(total, 'count') else 0
            
            # Get posted stories
            posted = supabase.table("posting_history")\
                .select("id", count="exact")\
                .gte("posted_at", cutoff)\
                .execute()
            
            posted_count = posted.count if hasattr(posted, 'count') else 0
            
            if total_count == 0:
                return True, "No recent stories (waiting for fetch)"
            
            success_rate = (posted_count / total_count) * 100 if total_count > 0 else 0
            
            if success_rate >= 30:
                return True, f"Success rate: {success_rate:.1f}% ({posted_count}/{total_count})"
            else:
                return False, f"Low success rate: {success_rate:.1f}% ({posted_count}/{total_count})"
        
        except Exception as e:
            return False, f"Error rate check failed: {str(e)}"
    
    def check_storage(self) -> Tuple[bool, str]:
        """Check database storage usage."""
        try:
            from app.db_pool import get_supabase_client
            supabase = get_supabase_client()
            
            # Count total stories
            result = supabase.table("stories").select("id", count="exact").execute()
            story_count = result.count if hasattr(result, 'count') else 0
            
            # Count total posts
            result = supabase.table("posting_history").select("id", count="exact").execute()
            post_count = result.count if hasattr(result, 'count') else 0
            
            # Estimate storage (rough calculation)
            # Average story ~2KB, posting_history ~0.5KB
            estimated_mb = (story_count * 2 + post_count * 0.5) / 1024
            
            if estimated_mb < 400:  # Supabase free tier is 500MB
                return True, f"Storage: ~{estimated_mb:.1f}MB ({story_count} stories, {post_count} posts)"
            else:
                return False, f"High storage: ~{estimated_mb:.1f}MB (consider cleanup)"
        
        except Exception as e:
            return False, f"Storage check error: {str(e)}"
    
    def run_all_checks(self) -> Dict[str, Dict]:
        """Run all health checks and return results."""
        logger.info("Starting comprehensive health check...")
        
        for check_name, check_func in self.checks:
            try:
                success, message = check_func()
                self.results[check_name] = {
                    "status": "PASS" if success else "FAIL",
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                status_icon = "✓" if success else "✗"
                logger.info(f"{status_icon} {check_name}: {message}")
            
            except Exception as e:
                self.results[check_name] = {
                    "status": "ERROR",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"✗ {check_name}: ERROR - {str(e)}")
        
        return self.results
    
    def get_overall_status(self) -> Tuple[str, List[str]]:
        """Get overall system status."""
        if not self.results:
            return "UNKNOWN", ["No checks run yet"]
        
        failures = [name for name, result in self.results.items() 
                   if result["status"] != "PASS"]
        
        if not failures:
            return "HEALTHY", []
        elif len(failures) <= 2:
            return "DEGRADED", failures
        else:
            return "CRITICAL", failures
    
    def format_report(self) -> str:
        """Format health check results as readable report."""
        if not self.results:
            return "No health check results available"
        
        status, failures = self.get_overall_status()
        
        report = f"\n{'='*60}\n"
        report += f"NEWS BOT HEALTH CHECK - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        report += f"{'='*60}\n\n"
        report += f"Overall Status: {status}\n\n"
        
        for check_name, result in self.results.items():
            icon = "✓" if result["status"] == "PASS" else "✗"
            report += f"{icon} {check_name}: {result['status']}\n"
            report += f"  └─ {result['message']}\n"
        
        if failures:
            report += f"\n⚠ Failed Checks: {', '.join(failures)}\n"
        
        report += f"\n{'='*60}\n"
        
        return report


def main():
    """Run health check from command line."""
    health = HealthCheck()
    health.run_all_checks()
    print(health.format_report())
    
    status, _ = health.get_overall_status()
    
    # Exit with appropriate code
    if status == "HEALTHY":
        sys.exit(0)
    elif status == "DEGRADED":
        sys.exit(1)
    else:  # CRITICAL
        sys.exit(2)


if __name__ == "__main__":
    main()
