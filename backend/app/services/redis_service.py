from functools import lru_cache

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def is_redis_available() -> bool:
    try:
        get_redis_client().ping()
        return True
    except RedisError:
        return False
