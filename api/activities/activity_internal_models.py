from datetime import date
from decimal import Decimal
from typing import Optional, List

from api.activities.activity_models import SimplenightActivity, ActivityLocation
from api.common.common_models import SimplenightModel
from api.hotel.models.booking_model import Locator
from api.hotel.models.hotel_api_model import Image
from api.hotel.models.hotel_common_models import Money
from api.locations.models import Location


class AdapterActivity(SimplenightModel):
    name: str
    provider: str
    code: str
    description: str
    activity_date: date
    total_price: Money
    location: Optional[ActivityLocation]
    categories: Optional[List[str]]
    images: List[Image]
    rating: Optional[Decimal]
    reviews: Optional[int]


class AdapterActivitySearch(SimplenightModel):
    begin_date: date
    end_date: date
    adults: int
    children: int
    provider: Optional[str] = None


class AdapterActivityLocationSearch(AdapterActivitySearch):
    location: Location
    provider_location_code: Optional[str]


class AdapterActivitySpecificSearch(AdapterActivitySearch):
    activity_id: str


class AdapterActivityBookingResponse(SimplenightModel):
    success: bool
    record_locator: Locator


class ActivityDataCachePayload(SimplenightModel):
    code: str
    provider: str
    price: Decimal
    currency: str
    adapter_activity: AdapterActivity
    simplenight_activity: SimplenightActivity
