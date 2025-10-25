# apps/shipping/cache_utils.py
import hashlib
import logging
from django.core.cache import cache
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def get_cache_key(prefix: str, request):
    """Generate a unique cache key based on user + URL + query params"""
    user_id = getattr(request.user, "id", "anon")
    path = request.get_full_path()
    hash_key = hashlib.md5(path.encode()).hexdigest()
    return f"{prefix}_{user_id}_{hash_key}"

def get_cached_response(prefix: str, request):
    """Try to get cached response"""
    cache_key = get_cache_key(prefix, request)
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"[CACHE HIT] key={cache_key}")
        return Response(cached_data)
    return None

def set_cached_response(prefix: str, request, data, timeout=60):
    """Save serialized response data to cache"""
    cache_key = get_cache_key(prefix, request)
    cache.set(cache_key, data, timeout=timeout)
    logger.info(f"[CACHE SET] key={cache_key}")

def invalidate_cache_patterns(patterns):
    """Delete all cache entries matching certain prefixes"""
    for pattern in patterns:
        cache.delete_pattern(f"{pattern}_*")
        logger.info(f"[CACHE INVALIDATED] pattern={pattern}_*")
