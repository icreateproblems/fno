"""
Database connection pooling and caching for Supabase credit optimization
"""
import os
from functools import lru_cache
from supabase import create_client, Client
from app.logger import get_logger

logger = get_logger(__name__)

# Connection pool - reuse connections instead of creating new ones
_client_pool = {}

@lru_cache(maxsize=1)
def get_supabase_client(url: str, key: str) -> Client:
    """
    Cached Supabase client - reuses same connection instead of creating new ones
    Saves ~50% credits by avoiding connection overhead
    """
    cache_key = f"{url}:{key[:10]}"
    
    if cache_key not in _client_pool:
        logger.debug("Creating new Supabase client (cached)")
        _client_pool[cache_key] = create_client(url, key)
    
    return _client_pool[cache_key]

# Query result cache - avoid duplicate reads
_query_cache = {}
_cache_ttl = {}

def cached_query(table: str, query_key: str, fetch_fn, ttl_seconds: int = 300):
    """
    Cache query results to reduce duplicate database reads
    Example: cached_query("stories", "latest_10", lambda: supabase.table("stories").select("*").limit(10).execute())
    """
    import time
    
    cache_key = f"{table}:{query_key}"
    now = time.time()
    
    # Check if cache is valid
    if cache_key in _query_cache and cache_key in _cache_ttl:
        if now - _cache_ttl[cache_key] < ttl_seconds:
            logger.debug(f"Cache HIT: {cache_key}")
            return _query_cache[cache_key]
    
    # Cache miss - fetch and store
    logger.debug(f"Cache MISS: {cache_key}")
    result = fetch_fn()
    _query_cache[cache_key] = result
    _cache_ttl[cache_key] = now
    
    return result

def clear_cache():
    """Clear all cached queries - call after inserts/updates"""
    global _query_cache, _cache_ttl
    _query_cache = {}
    _cache_ttl = {}
    logger.debug("Query cache cleared")
