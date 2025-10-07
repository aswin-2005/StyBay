# main.py
import json
import redis
from database import get_product_by_id

# ---------------- Redis Cloud Setup ---------------- #
redis_client = redis.Redis(
    host='redis-13049.c330.asia-south1-1.gce.redns.redis-cloud.com',
    port=13049,
    decode_responses=True,
    username="default",
    password="53qYqCKWmftIVsvM0dY9eYMMDMaZIHcg",
)


CACHE_TTL = 300  # seconds (5 minutes)


# ---------------- Cache Helpers ---------------- #

def set_product(product_id: str, product_data: dict):
    """
    Store product data in Redis cache with TTL.
    """
    redis_client.setex(f"product:{product_id}", CACHE_TTL, json.dumps(product_data))


def get_product(product_id: str):
    """
    Retrieve product data from Redis cache.
    Returns None if not cached.
    """
    data = redis_client.get(f"product:{product_id}")
    if data:
        return json.loads(data)
    return None