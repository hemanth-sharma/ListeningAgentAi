import redis

# r = redis.Redis(host="redis", port=6379, db=0) # on docker
r = redis.Redis(host="localhost", port=6379, db=0) # on local



def is_duplicate(mission_id: str, hash_key: str):
    key = f"dedup:{mission_id}"

    if r.sismember(key, hash_key):
        return True

    r.sadd(key, hash_key)
    return False