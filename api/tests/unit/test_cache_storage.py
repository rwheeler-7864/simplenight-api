from time import sleep

from django.test import SimpleTestCase

from api.common import cache_storage


class TestCacheStorage(SimpleTestCase):
    def test_cache_simple(self):
        cache_storage.set("foo", "bar")
        assert cache_storage.get("foo") == "bar"

    def test_cache_ttl(self):
        with self.settings(CACHE_TIMEOUT=1):
            cache_storage.set("foo", "bar")
            assert cache_storage.get("foo") == "bar"

            sleep(1)

            assert cache_storage.get("foo") is None
