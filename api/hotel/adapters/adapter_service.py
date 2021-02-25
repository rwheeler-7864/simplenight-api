from enum import Enum
from typing import List, Union

from api.activities.activity_adapter import ActivityAdapter
from api.activities.adapters.muse.muse_activity_adapter import MuseActivityAdapter
from api.activities.adapters.stub_activity_adapter import StubActivityAdapter
from api.activities.adapters.tiqets.tiqets_activity_adapter import TiqetsActivityAdapter
from api.activities.adapters.tourcms.tourcms_activity_adapter import TourCmsActivityAdapter
from api.activities.adapters.travelcurious.travelcurious_activity_adapter import TravelcuriousActivityAdapter
from api.activities.adapters.urban.urban_activity_adapter import UrbanActivityAdapter
from api.common.common_exceptions import FeatureNotFoundException
from api.common.request_context import get_config_bool, get_config
from api.hotel.adapters.hotel_adapter import HotelAdapter
from api.hotel.adapters.hotelbeds.hotelbeds_adapter import HotelbedsAdapter
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.stub.stub import StubHotelAdapter
from api.hotel.adapters.travelport.travelport import TravelportHotelAdapter
from api.hotel.models.hotel_api_model import HotelSearch
from api.models.models import Feature
from api.multi.multi_product_models import RestaurantSearch, ActivitySearch
from api.restaurants.adapters.stub_restaurant_adapter import StubRestaurantAdapter
from api.restaurants.restaurant_adapter import RestaurantAdapter
from api.view.exceptions import AvailabilityException, AvailabilityErrorCode


class AdapterType(Enum):
    HOTEL = "hotel"
    ACTIVITY = "activity"
    RESTAURANT = "restaurant"


ADAPTERS = {
    AdapterType.HOTEL: {
        "stub_hotel": StubHotelAdapter,
        "travelport": TravelportHotelAdapter,
        "hotelbeds": HotelbedsAdapter,
        "priceline": PricelineAdapter,
    },
    AdapterType.ACTIVITY: {
        "stub_activity": StubActivityAdapter,
        "tiqets": TiqetsActivityAdapter,
        "travelcurious": TravelcuriousActivityAdapter,
        "musement": MuseActivityAdapter,
        "urban": UrbanActivityAdapter,
        "tourcms": TourCmsActivityAdapter,
    },
    AdapterType.RESTAURANT: {"stub_restaurant": StubRestaurantAdapter},
}

ALL_ADAPTERS = {name: adapter for adapter_type in ADAPTERS for name, adapter in ADAPTERS[adapter_type].items()}


def get_adapter(name):
    return ALL_ADAPTERS.get(name).factory(get_test_mode())


def get_adapters(name, adapter_type=None) -> List[HotelAdapter]:
    if adapter_type is None:
        adapter_type = AdapterType.HOTEL

    return [get_adapter(x) for x in name.split(",") if x in ADAPTERS[adapter_type]]


def get_hotel_adapters_to_search(search_request: HotelSearch) -> List[HotelAdapter]:
    return get_adapters_for_type(search_request, adapter_type=AdapterType.HOTEL)


def get_activity_adapters_to_search(search_request: ActivitySearch) -> List[ActivityAdapter]:
    return get_adapters_for_type(search_request, adapter_type=AdapterType.ACTIVITY)


def get_restaurant_adapters_to_search(search_request: RestaurantSearch) -> List[RestaurantAdapter]:
    return get_adapters_for_type(search_request, adapter_type=AdapterType.RESTAURANT)


def get_activity_adapter(adapter_name: str) -> ActivityAdapter:
    return get_adapter(adapter_name)


def get_adapters_for_type(
    search_request, adapter_type=None
) -> List[Union[HotelAdapter, ActivityAdapter, RestaurantAdapter]]:
    """
    Returns a list of adapters to search, identified by their string name.
    If an adapter is explicitly specified in the request, return that.
    Otherwise, return the list of adapters enabled for a particular organization, if an
    organization is associated with the request (by API key).

    If no organization is associated, return the stub adapter.
    """

    if adapter_type is None:
        adapter_type = AdapterType.HOTEL

    if search_request.provider:
        if search_request.provider not in ADAPTERS[adapter_type]:
            raise AvailabilityException("Provider not found", AvailabilityErrorCode.PROVIDER_ERROR)

        return get_adapters(search_request.provider, adapter_type)

    enabled_adapters = get_enabled_connectors()
    if enabled_adapters:
        return get_adapters(enabled_adapters, adapter_type)

    if adapter_type == AdapterType.HOTEL:
        return get_adapters("stub_hotel", adapter_type)
    elif adapter_type == AdapterType.ACTIVITY:
        return get_adapters("stub_activity", adapter_type)
    elif adapter_type == AdapterType.RESTAURANT:
        return get_adapters("stub_restaurant", adapter_type)


def get_enabled_connectors():
    try:
        return get_config(Feature.ENABLED_ADAPTERS)
    except FeatureNotFoundException:
        pass


def get_test_mode():
    return get_config_bool(Feature.TEST_MODE)
