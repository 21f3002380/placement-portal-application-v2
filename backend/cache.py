import json
import functools
import redis
from flask import current_app

_client = None


def get_client():
    global _client
    if _client is None:
        url = current_app.config["CACHE_REDIS_URL"]
        _client = redis.Redis.from_url(url, decode_responses=True)
    return _client


def _safe(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except redis.RedisError:
            return None
    return wrapper


@_safe
def cache_get(key):
    val = get_client().get(key)
    return json.loads(val) if val is not None else None


@_safe
def cache_set(key, value, timeout=None):
    timeout = timeout or current_app.config["CACHE_DEFAULT_TIMEOUT"]
    get_client().setex(key, timeout, json.dumps(value))


@_safe
def cache_delete(key):
    get_client().delete(key)


@_safe
def cache_clear_prefix(prefix):
    client = get_client()
    for k in client.scan_iter(match=f"{prefix}*"):
        client.delete(k)


def cached(key_fn, timeout=None):
    """Decorator: key_fn(*args, **kwargs) -> cache key string."""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = cache_get(key)
            if hit is not None:
                return hit
            result = f(*args, **kwargs)
            cache_set(key, result, timeout)
            return result
        return wrapper
    return decorator
