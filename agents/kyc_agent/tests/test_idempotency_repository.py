import pytest
import fakeredis
from src.repositories.idempotency_repository import RedisIdempotencyRepository

@pytest.fixture
def repo():
    client = fakeredis.FakeRedis(decode_responses=True)
    return RedisIdempotencyRepository(client)

@pytest.mark.asyncio
async def test_save_and_get_response(repo):
    key = "test_key"
    response = {"status": "success", "data": 123}
    full_payload = {"request_hash": "abc", "response": response}
    
    await repo.save_response(key, full_payload)
    retrieved = await repo.get_response(key)
    
    assert retrieved == full_payload

@pytest.mark.asyncio
async def test_acquire_and_release_lock(repo):
    key = "lock_key"
    
    # First acquisition
    acquired = await repo.acquire_lock(key)
    assert acquired is True
    
    # Second acquisition should fail
    acquired_again = await repo.acquire_lock(key)
    assert acquired_again is False
    
    # Release and re-acquire
    await repo.release_lock(key)
    acquired_after_release = await repo.acquire_lock(key)
    assert acquired_after_release is True
