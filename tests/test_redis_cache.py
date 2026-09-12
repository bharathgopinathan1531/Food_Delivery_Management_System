from app.cache.redis_client import (
    set_cache,
    get_cache,
    delete_cache,
)


def test_redis_cache_set_and_get():
    key = "test:food_delivery"
    value = "Redis Working"

    set_cache(key, value)

    assert get_cache(key) == value

    delete_cache(key)


def test_redis_cache_delete():
    key = "test:delete"

    set_cache(key, "temporary")

    assert get_cache(key) == "temporary"

    delete_cache(key)

    assert get_cache(key) is None