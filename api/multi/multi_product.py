from concurrent.futures.thread import ThreadPoolExecutor
from threading import currentThread
from typing import Dict, Type, Callable, List

from django.db import connection

from api import logger
from api.activities import activity_service
from api.activities.activity_models import (
    SimplenightActivity,
    SimplenightActivityDetailRequest,
    SimplenightActivityDetailResponse,
    SimplenightActivityVariantRequest,
    ActivityVariants,
)
from api.common import request_cache
from api.common.request_context import get_config
from api.hotel import hotel_service
from api.hotel.models.hotel_api_model import HotelLocationSearch, HotelSpecificSearch, SimplenightHotel
from api.models.models import Feature
from api.multi.multi_product_models import (
    SearchRequest,
    RestaurantSearch,
    SearchResponse,
    ActivityLocationSearch,
    ActivitySpecificSearch,
)
from api.restaurants import restaurant_search
from api.restaurants.restaurant_models import SimplenightRestaurant
from api.view.exceptions import AvailabilityException, AvailabilityErrorCode

search_map: Dict[Type, Callable] = {
    HotelLocationSearch: hotel_service.search_by_location,
    HotelSpecificSearch: hotel_service.search_by_id,
    ActivityLocationSearch: activity_service.search_by_location,
    ActivitySpecificSearch: activity_service.search_by_id,
    RestaurantSearch: restaurant_search.search,
}


def search_request(search: SearchRequest):
    searches = filter(None, [search.hotel_search, search.activity_search, search.restaurant_search])

    response = SearchResponse()
    parent_thread_name = currentThread()

    def thread_initializer():
        request_cache.copy_request_cache(parent_thread_name)
        logger.info(f"Initializing thread.  Test Mode: {get_config(Feature.TEST_MODE)}")

    def search_fn(x):
        try:
            return search_map.get(x.__class__)(x)
        finally:
            connection.close()

    logger.info(f"Launching searches for {search.product_types}")
    get_config(Feature.TEST_MODE)  # TODO: HACK to make sure feature is in cache
    with ThreadPoolExecutor(max_workers=5, initializer=thread_initializer) as executor:
        futures = []
        for search in searches:
            futures.append(executor.submit(search_fn, search))

        for future in futures:
            try:
                _set_result_on_response(response, future.result(timeout=30))
            except Exception:
                logger.exception("Exception while searching adapter")

        executor.shutdown()

    return response


def details(request: SimplenightActivityDetailRequest) -> SimplenightActivityDetailResponse:
    try:
        return activity_service.details(request)
    except Exception as e:
        logger.exception("Error while searching activity details")
        raise AvailabilityException(detail=str(e), error_type=AvailabilityErrorCode.PROVIDER_ERROR)


def variants(request: SimplenightActivityVariantRequest) -> List[ActivityVariants]:
    try:
        return activity_service.variants(request)
    except Exception as e:
        logger.exception("Error while searching activity variants")
        raise AvailabilityException(detail=str(e), error_type=AvailabilityErrorCode.PROVIDER_ERROR)


def _set_result_on_response(response, result):
    if not result:
        return

    result_for_test = result
    if isinstance(result, list):
        result_for_test = result[0]

    if isinstance(result_for_test, SimplenightHotel):
        response.hotel_results = result
    elif isinstance(result_for_test, SimplenightActivity):
        response.activity_results = result
    elif isinstance(result_for_test, SimplenightRestaurant):
        response.restaurant_results = result
