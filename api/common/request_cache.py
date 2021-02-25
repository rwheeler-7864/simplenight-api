from threading import currentThread
from typing import Any

from django.core.cache.backends.locmem import LocMemCache
from django.utils.deprecation import MiddlewareMixin

_request_cache = {}
_installed_middleware = False


# Just used for type hinting
class CacheStorageTypeHint:
    def get(self, name: str):
        pass

    def set(self, name: str, value: Any):
        pass


def get_request_cache() -> CacheStorageTypeHint:
    assert _installed_middleware, "RequestCacheMiddleware not loaded"
    if currentThread() not in _request_cache:
        _request_cache[currentThread()] = RequestCache()

    return _request_cache[currentThread()]


def copy_request_cache(thread_name):
    _request_cache[currentThread()] = _request_cache[thread_name]


class RequestCache(LocMemCache):
    def __init__(self):
        name = "locmemcache@%i" % hash(currentThread())
        params = dict()
        super(RequestCache, self).__init__(name, params)


class RequestCacheMiddleware(MiddlewareMixin):
    """
    Creates a LocMem cache, keyed by current thread name, and clears the cache at beginning/end of request
    """

    def __init__(self, handler):
        super().__init__(handler)
        global _installed_middleware
        _installed_middleware = True

    @staticmethod
    def process_request(_request):
        if currentThread() not in _request_cache:
            _request_cache[currentThread()] = RequestCache()

        _request_cache[currentThread()].clear()

    @staticmethod
    def process_response(_request, _response):
        _request_cache[currentThread()].clear()

        return _response
