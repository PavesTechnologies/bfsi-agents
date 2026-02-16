import redis

try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    if r.ping():
        print("Redis is running and accessible.")
    else:
        print("Redis ping failed.")
except Exception as e:
    print(f"Redis connection error: {e}")
