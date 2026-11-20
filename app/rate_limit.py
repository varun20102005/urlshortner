
from app.cache import redis_client


def check_rate_limit(key: str, limit: int = 5, window: int = 60):
    """
    Allow a maximum number of requests within a time window.

    limit: maximum requests
    window: window duration in seconds
    """

    lua_script = """
    local current = redis.call('INCR', KEYS[1])

    if current == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end

    return current
    """

    try:
        current = redis_client.eval(
            lua_script,
            1,
            key,
            window
        )

        return current <= limit

    except Exception:
        # Fail open: allow the request if Redis is unavailable.
        # The application's other functionality can continue.
        return True
