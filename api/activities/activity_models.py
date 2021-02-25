from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Union, Dict

from pydantic import Field

from api.common.common_models import SimplenightModel, BusinessContact
from api.hotel.models.hotel_api_model import Image
from api.hotel.models.hotel_common_models import Money


class ActivityLocation(SimplenightModel):
    address: str
    latitude: Decimal
    longitude: Decimal


class SimplenightActivity(SimplenightModel):
    name: str
    code: str
    description: str
    activity_date: date
    total_price: Money
    location: Optional[ActivityLocation]
    categories: Optional[List[str]]
    images: List[Image]
    rating: Optional[Decimal]
    reviews: Optional[int]


class ActivityAvailabilityTime(SimplenightModel):
    type: str
    label: str
    activity_dates: List[Union[datetime, date, str]]
    activity_times: List[str]
    capacity: int
    uuid: str


class ActivityCancellation(SimplenightModel):
    type: str
    label: str


class ActivityItem(SimplenightModel):
    category: Optional[Union[str, List[str]]] = Field(default_factory=list)
    code: str
    status: str
    price: Decimal
    price_type: str


class ActivityVariant(SimplenightModel):
    def __hash__(self):  # make hashable for use in a set
        return hash((self.code, self.name, self.price))

    code: str
    name: str
    description: str
    price: Decimal
    capacity: int
    additional: Optional[Dict[str, str]]


class ActivityVariants(SimplenightModel):
    variants: Dict[str, List[ActivityVariant]]


class SimplenightActivityVariantRequest(SimplenightModel):
    code: str
    activity_date: date


class SimplenightActivityDetailRequest(SimplenightModel):
    code: str
    date_from: date
    date_to: date


class SimplenightActivityDetailResponse(SimplenightModel):
    code: str
    type: str
    categories: List[str]
    timezone: str
    images: List[Image]
    contact: BusinessContact
    locations: Optional[ActivityLocation]
    availabilities: List[date]
    policies: List[str]
    cancellations: List[ActivityCancellation]
