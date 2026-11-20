import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

def get_cache(key):
    try:
        return redis_client.get(key)
    except redis.RedisError:
        return None

def set_cache(key, value, expiry=300):
    try:
        redis_client.set(key, value, ex=expiry)
    except redis.RedisError:
        pass

def delete_cache(key):
    try:
        redis_client.delete(key)
    except redis.RedisError:
        pass