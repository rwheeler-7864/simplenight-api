import distutils.util
import time
from collections import Callable
from threading import RLock

from cachetools import cached, LRUCache

from api.common.common_exceptions import FeatureNotFoundException
from api.common.request_cache import get_request_cache
from api.models.models import Organization, Feature

cache = LRUCache(maxsize=65536)
lock = RLock()


class RequestContext:
    """Wrapper around RequestCache for consistent key usage"""

    def __init__(self, cache):
        self.cache = cache

    def get_organization(self) -> Organization:
        return self.cache.get("organization")

    def get_request_id(self) -> str:
        return self.cache.get("request_id")


def get_request_context():
    return RequestContext(get_request_cache())


def get_config(feature: Feature, transform_fn: Callable = None):
    request_context = get_request_context()
    organization = request_context.get_organization()

    def get_ttl_hash(seconds=30):
        """Return the same value withing `seconds` time period"""
        return round(time.time() / seconds)

    def get_cache_key():
        return f"{organization.name}.{feature.name}.{get_ttl_hash()}"

    @cached(cache=cache, lock=lock, key=get_cache_key)
    def _get_config():
        feature_value = organization.get_feature(feature)
        if not feature_value:
            raise FeatureNotFoundException(feature)
        elif transform_fn:
            return transform_fn(feature_value)
        else:
            return feature_value

    return _get_config()


def get_config_bool(feature: Feature) -> bool:
    return get_config(feature, transform_fn=distutils.util.strtobool)


def get_config_bool_default(feature: Feature, default: bool):
    try:
        return get_config_bool(feature)
    except FeatureNotFoundException:
        return default


def clear_cache():
    cache.clear()


def get_test_mode():
    return get_config_bool(Feature.TEST_MODE)
