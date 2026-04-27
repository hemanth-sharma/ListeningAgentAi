import redis

from app.config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def is_duplicate(mission_id: str, hash_key: str) -> bool:
    key = f"dedup:{mission_id}"
    added = r.sadd(key, hash_key)
    return added == 0