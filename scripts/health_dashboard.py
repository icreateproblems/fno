"""
System health monitoring and status dashboard.
Track performance metrics, error rates, API health.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger

logger = get_logger(__name__)

class HealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.metrics_file = "health_metrics.json"
    
    def check_system_health(self) -> Dict:
        """
        Comprehensive system health check.
        
        Returns health status with metrics:
        - API availability
        - Database connectivity
        - Error rates
        - Posting success rate
        - Performance metrics
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check 1: Database connectivity
        db_health = self._check_database()
        health_status['components']['database'] = db_health
        
        # Check 2: Groq API availability
        groq_health = self._check_groq_api()
        health_status['components']['groq_api'] = groq_health
        
        # Check 3: Instagram connectivity
        ig_health = self._check_instagram()
        health_status['components']['instagram'] = ig_health
        
        # Check 4: Posting success rate (last 24h)
        posting_health = self._check_posting_rate()
        health_status['components']['posting'] = posting_health
        
        # Check 5: Error rate
        error_health = self._check_error_rate()
        health_status['components']['errors'] = error_health
        
        # Determine overall status
        component_statuses = [
            comp['status'] for comp in health_status['components'].values()
        ]
        
        if all(s == 'healthy' for s in component_statuses):
            health_status['overall_status'] = 'healthy'
        elif any(s == 'critical' for s in component_statuses):
            health_status['overall_status'] = 'critical'
        else:
            health_status['overall_status'] = 'degraded'
        
        # Log status
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'critical': '🚨'
        }
        
        logger.info(
            f"{status_emoji[health_status['overall_status']]} "
            f"System Health: {health_status['overall_status'].upper()}"
        )
        
        # Save metrics
        self._save_metrics(health_status)
        
        return health_status
    
    def _check_database(self) -> Dict:
        """Check database connectivity and performance"""
        try:
            start = datetime.now()
            result = self.supabase.table("stories").select("id").limit(1).execute()
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            if latency_ms < 200:
                status = 'healthy'
            elif latency_ms < 500:
                status = 'degraded'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'latency_ms': round(latency_ms, 2),
                'message': f'Database responding in {latency_ms:.0f}ms'
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    def _check_groq_api(self) -> Dict:
        """Check Groq API availability"""
        try:
            import requests
            from app.config import GROQ_API_KEY
            
            start = datetime.now()
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            latency_ms = (datetime.now() - start).total_seconds() * 1000
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'latency_ms': round(latency_ms, 2),
                    'message': 'Groq API responding normally'
                }
            else:
                return {
                    'status': 'degraded',
                    'status_code': response.status_code,
                    'message': f'Groq API returned {response.status_code}'
                }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Groq API unavailable'
            }
    
    def _check_instagram(self) -> Dict:
        """Check Instagram session validity"""
        try:
            from app.config import INSTAGRAM_SESSION_FILE
            
            if not os.path.exists(INSTAGRAM_SESSION_FILE):
                return {
                    'status': 'critical',
                    'message': 'Instagram session file missing'
                }
            
            # Check file age
            file_age_hours = (
                time.time() - os.path.getmtime(INSTAGRAM_SESSION_FILE)
            ) / 3600
            
            if file_age_hours > 168:  # 7 days
                return {
                    'status': 'degraded',
                    'message': f'Session is {file_age_hours:.0f}h old - may need refresh'
                }
            
            return {
                'status': 'healthy',
                'message': f'Session valid ({file_age_hours:.0f}h old)'
            }
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Could not check Instagram status'
            }
    
    def _check_posting_rate(self) -> Dict:
        """Check posting success rate in last 24h"""
        try:
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            
            posts = self.supabase.table("posting_history").select(
                "success"
            ).gte("created_at", cutoff).execute().data
            
            if not posts:
                return {
                    'status': 'degraded',
                    'message': 'No posts in last 24h'
                }
            
            success_count = sum(1 for p in posts if p.get('success'))
            total_count = len(posts)
            success_rate = (success_count / total_count) * 100
            
            if success_rate >= 90:
                status = 'healthy'
            elif success_rate >= 70:
                status = 'degraded'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'success_rate': round(success_rate, 1),
                'posts_24h': total_count,
                'message': f'{success_rate:.0f}% success rate ({success_count}/{total_count})'
            }
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Could not check posting rate'
            }
    
    def _check_error_rate(self) -> Dict:
        """Check error rate from logs"""
        try:
            # Check error log file
            error_log = "error_history.json"
            if not os.path.exists(error_log):
                return {
                    'status': 'healthy',
                    'message': 'No errors logged'
                }
            
            with open(error_log, 'r') as f:
                errors = json.load(f)
            
            # Count errors in last hour
            cutoff = datetime.now() - timedelta(hours=1)
            recent_errors = [
                e for e in errors
                if datetime.fromisoformat(e['timestamp']) > cutoff
            ]
            
            error_count = len(recent_errors)
            
            if error_count == 0:
                status = 'healthy'
            elif error_count <= 3:
                status = 'degraded'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'errors_last_hour': error_count,
                'message': f'{error_count} errors in last hour'
            }
        except Exception as e:
            return {
                'status': 'healthy',
                'message': 'Error log not available'
            }
    
    def _save_metrics(self, health_status: Dict):
        """Save health metrics to file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = []
            
            metrics.append(health_status)
            
            # Keep last 1000 checks
            metrics = metrics[-1000:]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save metrics: {e}")
    
    def generate_health_report(self) -> str:
        """Generate human-readable health report"""
        health = self.check_system_health()
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║           FASTNEWSORG SYSTEM HEALTH REPORT              ║
╠══════════════════════════════════════════════════════════╣
║ Status: {health['overall_status'].upper()}                                     ║
║ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                          ║
╠══════════════════════════════════════════════════════════╣
║ DATABASE                                                 ║
║   Status: {health['components']['database']['status']}
║   {health['components']['database']['message']}
╠══════════════════════════════════════════════════════════╣
║ GROQ API                                                 ║
║   Status: {health['components']['groq_api']['status']}
║   {health['components']['groq_api']['message']}
╠══════════════════════════════════════════════════════════╣
║ INSTAGRAM                                                ║
║   Status: {health['components']['instagram']['status']}
║   {health['components']['instagram']['message']}
╠══════════════════════════════════════════════════════════╣
║ POSTING                                                  ║
║   Status: {health['components']['posting']['status']}
║   {health['components']['posting']['message']}
╠══════════════════════════════════════════════════════════╣
║ ERRORS                                                   ║
║   Status: {health['components']['errors']['status']}
║   {health['components']['errors']['message']}
╚══════════════════════════════════════════════════════════╝
"""
        return report


if __name__ == "__main__":
    # Test health monitoring
    from app.config import SUPABASE_URL, SUPABASE_KEY
    from supabase import create_client
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    monitor = HealthMonitor(supabase)
    
    print(monitor.generate_health_report())
