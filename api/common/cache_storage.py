"""
Thin wrapper around Django cache, initially simply to control timeouts
"""
from typing import Any

from django.conf import settings
from django.core.cache import cache


# noinspection PyShadowingBuiltins
def set(key: str, value: Any, timeout=None):
    if timeout is None:
        timeout = _timeout()

    cache.set(key, value, timeout=timeout)


def get(key: str):
    return cache.get(key)


def unset(key: str):
    cache.delete(key)


def exists(key: str) -> bool:
    return key in cache


def _timeout():
    return settings.CACHE_TIMEOUT
