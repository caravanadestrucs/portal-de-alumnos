"""
Shared extensions for Flask app
"""
import os
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def _get_limiter_storage():
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        return redis_url
    # memory fallback — single instance only
    logging.getLogger(__name__).warning("REDIS_URL not set — using memory:// for rate limiter (single-instance)")
    return "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_get_limiter_storage(),
)
