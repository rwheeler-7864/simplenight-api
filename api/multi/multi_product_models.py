from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union

from api.activities.activity_models import SimplenightActivity
from api.common.common_models import SimplenightModel
from api.hotel.models.hotel_api_model import SimplenightHotel, HotelLocationSearch, HotelSpecificSearch
from api.restaurants.restaurant_models import SimplenightRestaurant


class Products(Enum):
    HOTELS = "hotels"
    ACTIVITIES = "activities"
    DINING = "dining"
    EVENTS = "events"


class ActivitySearch(SimplenightModel):
    begin_date: date
    end_date: date
    adults: int
    children: int = 0
    provider: Optional[str] = None


class RestaurantSearch(SimplenightModel):
    location_id: str
    reservation_date: datetime
    party_size: int
    cuisine: Optional[str] = None
    restaurant_name: Optional[str] = None
    provider: Optional[str] = None


class ActivityLocationSearch(ActivitySearch):
    location_id: Union[str, int]


class ActivitySpecificSearch(ActivitySearch):
    activity_id: str


class SearchRequest(SimplenightModel):
    product_types: List[Products]
    hotel_search: Optional[Union[HotelLocationSearch, HotelSpecificSearch]]
    activity_search: Optional[Union[ActivitySpecificSearch, ActivityLocationSearch]]
    restaurant_search: Optional[RestaurantSearch]


class SearchResponse(SimplenightModel):
    hotel_results: Optional[Union[SimplenightHotel, List[SimplenightHotel]]]
    restaurant_results: Optional[List[SimplenightRestaurant]]
    activity_results: Optional[Union[SimplenightActivity, List[SimplenightActivity]]]
