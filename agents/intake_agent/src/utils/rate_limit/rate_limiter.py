import time
import redis

from src.core.config import get_settings

settings = get_settings()

redis_client = r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
    username=settings.REDIS_USERNAME,
    password=settings.REDIS_PASSWORD,
)
class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds

    def is_allowed(self, key: str):
        now = int(time.time())
        window_start = now - self.window

        pipe = redis_client.pipeline()

        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window)

        _, _, count, _ = pipe.execute()

        return count <= self.limit

# redis_client.set('foo', 'bar')
# print(redis_client.get('foo'))  # Output: b'bar'

# redis_client.flushdb()  # Clear the database for testing
# print("Database cleared. Current keys:", redis_client.keys())  # Should print an empty list


# keys = redis_client.keys("*") # Fetch all keys in the database
# print(keys)