"""
Advanced error handling and recovery system.
Automatically handles failures and retries with exponential backoff.
"""
import os
import sys
import time
import traceback
from typing import Callable, Any, Optional, Dict
from datetime import datetime
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger
from app.alerts import alert_manager

logger = get_logger(__name__)

class ErrorRecovery:
    """Intelligent error recovery with multiple strategies"""
    
    def __init__(self):
        self.error_log_file = "error_history.json"
        self.max_retries = 3
        self.base_delay = 2  # seconds
    
    def with_retry(
        self,
        max_attempts: int = 3,
        exponential_backoff: bool = True,
        recoverable_errors: tuple = (Exception,)
    ):
        """
        Decorator for automatic retry with exponential backoff.
        
        Usage:
            @error_recovery.with_retry(max_attempts=3)
            def risky_function():
                # code that might fail
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_error = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        result = func(*args, **kwargs)
                        
                        # Success - reset error count if needed
                        if attempt > 1:
                            logger.info(
                                f"✓ {func.__name__} succeeded on attempt {attempt}/{max_attempts}"
                            )
                        
                        return result
                        
                    except recoverable_errors as e:
                        last_error = e
                        
                        if attempt < max_attempts:
                            # Calculate delay
                            if exponential_backoff:
                                delay = self.base_delay * (2 ** (attempt - 1))
                            else:
                                delay = self.base_delay
                            
                            logger.warning(
                                f"⚠️ {func.__name__} failed (attempt {attempt}/{max_attempts}): {str(e)}"
                            )
                            logger.info(f"Retrying in {delay}s...")
                            
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"❌ {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                            )
                
                # All retries exhausted
                self._log_error(func.__name__, last_error)
                raise last_error
            
            return wrapper
        return decorator
    
    def handle_critical_error(
        self,
        error: Exception,
        context: str,
        notify: bool = True
    ):
        """
        Handle critical errors that require immediate attention.
        Logs error, sends alerts, and attempts graceful degradation.
        """
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        # Log to file
        self._log_error(context, error)
        
        # Log to console
        logger.error(f"🚨 CRITICAL ERROR in {context}")
        logger.error(f"   Type: {error_details['error_type']}")
        logger.error(f"   Message: {error_details['error_message']}")
        
        # Send alert if configured
        if notify:
            alert_manager.alert_critical_error(
                context,
                error_details
            )
        
        # Return error details for potential recovery
        return error_details
    
    def _log_error(self, function_name: str, error: Exception):
        """Log error to history file for analysis"""
        import json
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'function': function_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        try:
            # Load existing errors
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            # Add new error
            errors.append(error_entry)
            
            # Keep only last 100 errors
            errors = errors[-100:]
            
            # Save
            with open(self.error_log_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not log error to file: {e}")
    
    def graceful_degradation(
        self,
        primary_function: Callable,
        fallback_function: Optional[Callable] = None,
        default_value: Any = None
    ) -> Any:
        """
        Try primary function, fall back to alternative if it fails.
        
        Usage:
            result = error_recovery.graceful_degradation(
                primary_function=risky_api_call,
                fallback_function=use_cached_data,
                default_value={}
            )
        """
        try:
            return primary_function()
        except Exception as e:
            logger.warning(
                f"Primary function failed: {e}. "
                f"Attempting fallback..."
            )
            
            if fallback_function:
                try:
                    return fallback_function()
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    return default_value
            else:
                return default_value


# Global instance
error_recovery = ErrorRecovery()


# Usage examples:
@error_recovery.with_retry(max_attempts=3, exponential_backoff=True)
def post_to_instagram(image_path, caption):
    """Example function with automatic retry"""
    # Instagram API call here
    pass


def safe_database_operation(supabase, query_func):
    """Example of graceful degradation with database"""
    return error_recovery.graceful_degradation(
        primary_function=lambda: query_func(supabase),
        fallback_function=lambda: load_from_cache(),
        default_value=[]
    )
