# src/repositories/idempotency_repository.py

from redis import Redis


class RedisIdempotencyRepository:
    def __init__(self, redis_client: Redis, prefix: str = "kyc_lock"):
        self.redis = redis_client
        self.prefix = prefix

    def _lock_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def acquire_lock(self, key: str, ttl: int = 60) -> bool:
        return bool(self.redis.set(self._lock_key(key), "LOCKED", ex=ttl, nx=True))

    async def release_lock(self, key: str) -> None:
        self.redis.delete(self._lock_key(key))
