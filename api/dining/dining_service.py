from typing import List

from api.dining.adapters.yelp.yelp_adapter import YelpAdapter
from api.models.models import Feature
from api.common.request_context import get_config_bool
from api.dining.models.dining_api_model import (
    AdapterDining,
    AdapterOpening,
    DiningSearch,
    OpeningSearch,
    DiningDetail,
    DiningReview,
    DiningReservationRequest,
    DiningReservation,
    AdapterCancelRequest,
    IdSearch,
)

ADAPTERS = {
    "yelp": YelpAdapter,
}

def get_adapter(name = "yelp"):
    return ADAPTERS[name].factory(get_test_mode())

def get_adapters(name = "yelp"):
    return [get_adapter(x) for x in name.split(",") if x in ADAPTERS]

def get_test_mode():
    return get_config_bool(Feature.TEST_MODE)

# TODO: use get_adapters to iterate all adapters and get result
def get_businesses(search: DiningSearch) -> List[AdapterDining]:
    return get_adapter().get_businesses(search)

# TODO: use get_adapters to iterate all adapters and get result
def get_openings(search: OpeningSearch) -> List[AdapterOpening]:
    return get_adapter().get_openings(search)

# TODO: use get_adapters to iterate all adapters and get result
def details(search: IdSearch) -> DiningDetail:
    return get_adapter().details(search)

# TODO: use get_adapters to iterate all adapters and get result
def reviews(search: IdSearch) -> DiningReview:
    return get_adapter().reviews(search)

# TODO: use get_adapters to iterate all adapters and get result
def book(request: DiningReservationRequest) -> DiningReview:
    return get_adapter().book(request)

# TODO: use get_adapters to iterate all adapters and get result
def cancel(booking_id: str):
    return get_adapter().cancel(booking_id)