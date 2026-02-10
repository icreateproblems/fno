"""
API Key Manager - Multi-key rotation for high-volume usage
Prevents exhaustion by rotating through multiple API keys
"""
import os
import random
from typing import List, Optional
from app.logger import get_logger

logger = get_logger(__name__)


class APIKeyManager:
    """Manage multiple API keys with rotation strategies"""
    
    def __init__(self, keys: List[str], service_name: str = "API"):
        self.keys = [k.strip() for k in keys if k.strip()]
        self.service_name = service_name
        self.current_index = 0
        self.failed_keys = set()
        
        if not self.keys:
            raise ValueError(f"No valid {service_name} keys provided")
        
        logger.info(f"✓ {service_name} Key Manager initialized with {len(self.keys)} keys")
    
    def get_next_key(self, strategy: str = "round_robin") -> Optional[str]:
        """
        Get next available key using specified strategy.
        
        Strategies:
        - round_robin: Rotate through keys sequentially
        - random: Pick random key each time
        - failover: Use same key until it fails, then switch
        """
        available_keys = [k for k in self.keys if k not in self.failed_keys]
        
        if not available_keys:
            logger.warning(f"⚠️ All {self.service_name} keys failed! Resetting...")
            self.failed_keys.clear()
            available_keys = self.keys
        
        if strategy == "round_robin":
            key = available_keys[self.current_index % len(available_keys)]
            self.current_index = (self.current_index + 1) % len(available_keys)
            return key
        
        elif strategy == "random":
            return random.choice(available_keys)
        
        elif strategy == "failover":
            # Always use first available key until it fails
            return available_keys[0]
        
        return available_keys[0]
    
    def mark_key_failed(self, key: str):
        """Mark a key as failed (quota exhausted, invalid, etc)"""
        self.failed_keys.add(key)
        logger.warning(f"⚠️ {self.service_name} key marked as failed (total failed: {len(self.failed_keys)}/{len(self.keys)})")
    
    def reset_failed_keys(self):
        """Reset all failed keys (useful for daily quota resets)"""
        count = len(self.failed_keys)
        self.failed_keys.clear()
        if count > 0:
            logger.info(f"✓ Reset {count} failed {self.service_name} keys")
    
    @classmethod
    def from_env(cls, env_var_name: str, service_name: str = "API", separator: str = ","):
        """
        Create manager from environment variable.
        
        Example:
            GROQ_API_KEYS=key1,key2,key3
            manager = APIKeyManager.from_env("GROQ_API_KEYS", "Groq")
        """
        keys_str = os.getenv(env_var_name, "")
        
        if not keys_str:
            # Fallback to singular key
            single_key = os.getenv(env_var_name.rstrip('S'), "")
            if single_key:
                logger.info(f"Using single {service_name} key (consider adding multiple for redundancy)")
                return cls([single_key], service_name)
            raise ValueError(f"No {service_name} keys found in environment")
        
        keys = keys_str.split(separator)
        return cls(keys, service_name)


# Global managers (initialized on first use)
_groq_manager: Optional[APIKeyManager] = None
_newsapi_manager: Optional[APIKeyManager] = None


def get_groq_key() -> str:
    """Get next Groq API key"""
    global _groq_manager
    
    if _groq_manager is None:
        try:
            _groq_manager = APIKeyManager.from_env("GROQ_API_KEYS", "Groq")
        except ValueError:
            # Fallback to single key
            single_key = os.getenv("GROQ_API_KEY", "")
            if not single_key:
                raise ValueError("No Groq API keys configured")
            _groq_manager = APIKeyManager([single_key], "Groq")
    
    return _groq_manager.get_next_key(strategy="round_robin")


def get_newsapi_key() -> str:
    """Get next NewsAPI key"""
    global _newsapi_manager
    
    if _newsapi_manager is None:
        try:
            _newsapi_manager = APIKeyManager.from_env("NEWSAPI_KEYS", "NewsAPI")
        except ValueError:
            # Fallback to single key
            single_key = os.getenv("NEWSAPI_KEY", "")
            if not single_key:
                raise ValueError("No NewsAPI keys configured")
            _newsapi_manager = APIKeyManager([single_key], "NewsAPI")
    
    return _newsapi_manager.get_next_key(strategy="round_robin")


def mark_groq_key_failed(key: str):
    """Mark a Groq key as failed"""
    if _groq_manager:
        _groq_manager.mark_key_failed(key)


def mark_newsapi_key_failed(key: str):
    """Mark a NewsAPI key as failed"""
    if _newsapi_manager:
        _newsapi_manager.mark_key_failed(key)


def reset_all_keys():
    """Reset all failed keys (call on daily schedule)"""
    if _groq_manager:
        _groq_manager.reset_failed_keys()
    if _newsapi_manager:
        _newsapi_manager.reset_failed_keys()
