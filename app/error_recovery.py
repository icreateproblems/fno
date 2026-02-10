"""
Automated error recovery and retry mechanisms.
Provides resilient API calls with exponential backoff and circuit breaker.
"""

import time
import functools
from typing import Callable, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.logger import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """Execute function with circuit breaker protection."""
        
        # Check if circuit is open
        if self.state == "OPEN":
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker HALF_OPEN for {func.__name__}")
            else:
                logger.warning(f"Circuit breaker OPEN for {func.__name__}, blocking call")
                return False, None
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info(f"Circuit breaker CLOSED for {func.__name__}")
            
            return True, result
        
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.utcnow()
            
            logger.error(f"Circuit breaker failure {self.failures}/{self.failure_threshold} for {func.__name__}: {str(e)}")
            
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker OPEN for {func.__name__} after {self.failures} failures")
            
            return False, None
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple = (Exception,)
):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default=None, log_errors: bool = True, **kwargs) -> Any:
    """
    Safely execute a function and return default value on error.
    
    Args:
        func: Function to execute
        default: Default value to return on error
        log_errors: Whether to log errors
        *args, **kwargs: Arguments to pass to function
    
    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {str(e)}")
        return default


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def allow_request(self) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Block until request can be made."""
        while not self.allow_request():
            time.sleep(0.1)
    
    def get_wait_time(self) -> float:
        """Get seconds to wait before next request."""
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return max(0.0, self.time_window - (time.time() - oldest_call))


class ErrorTracker:
    """Track and analyze error patterns."""
    
    def __init__(self, window_size: int = 100):
        self.errors = []
        self.window_size = window_size
    
    def record_error(self, error_type: str, message: str):
        """Record an error occurrence."""
        self.errors.append({
            "type": error_type,
            "message": message,
            "timestamp": datetime.utcnow()
        })
        
        # Keep only recent errors
        if len(self.errors) > self.window_size:
            self.errors = self.errors[-self.window_size:]
    
    def get_error_rate(self, minutes: int = 10) -> float:
        """Get error rate (errors per minute) in recent window."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent_errors = [e for e in self.errors if e["timestamp"] > cutoff]
        
        return len(recent_errors) / minutes if minutes > 0 else 0
    
    def get_most_common_errors(self, limit: int = 5) -> list:
        """Get most common error types."""
        error_counts = {}
        
        for error in self.errors:
            error_type = error["type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_errors[:limit]
    
    def should_alert(self, threshold: float = 1.0) -> bool:
        """Check if error rate exceeds alert threshold."""
        return self.get_error_rate(minutes=10) > threshold


# Global instances
groq_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=300)  # 5 min timeout
supabase_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=180)  # 3 min timeout
groq_rate_limiter = RateLimiter(max_calls=30, time_window=60)  # 30 calls per minute
error_tracker = ErrorTracker()


def resilient_groq_call(func: Callable) -> Callable:
    """Decorator for GROQ API calls with full resilience."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Wait for rate limit
        groq_rate_limiter.wait_if_needed()
        
        # Apply circuit breaker
        @retry_with_backoff(max_retries=3, initial_delay=2.0)
        def protected_call():
            success, result = groq_circuit_breaker.call(func, *args, **kwargs)
            if not success:
                raise Exception("Circuit breaker open")
            return result
        
        try:
            return protected_call()
        except Exception as e:
            error_tracker.record_error("GROQ_API", str(e))
            logger.error(f"GROQ API call failed after all retries: {str(e)}")
            raise
    
    return wrapper


def resilient_supabase_call(func: Callable) -> Callable:
    """Decorator for Supabase calls with full resilience."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Apply circuit breaker
        @retry_with_backoff(max_retries=2, initial_delay=1.0)
        def protected_call():
            success, result = supabase_circuit_breaker.call(func, *args, **kwargs)
            if not success:
                raise Exception("Circuit breaker open")
            return result
        
        try:
            return protected_call()
        except Exception as e:
            error_tracker.record_error("SUPABASE", str(e))
            logger.error(f"Supabase call failed after all retries: {str(e)}")
            raise
    
    return wrapper
