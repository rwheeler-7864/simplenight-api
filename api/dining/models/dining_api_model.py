import decimal
from datetime import date, datetime
from typing import List, Optional
from pydantic import Field

from api.common.common_models import SimplenightModel, BusinessLocation


class DiningBase(SimplenightModel):
    date: Optional[str] = None
    time: Optional[str] = None
    covers: Optional[int] = None
    currency: Optional[str] = "USD"


class DiningSearch(DiningBase):
    latitude: Optional[decimal.Decimal] = None
    longitude: Optional[decimal.Decimal] = None


class AdapterDining(SimplenightModel):
    dining_id: str
    name: str
    image: str
    rating: float
    location: BusinessLocation
    phone: str
    openings: Optional[List[str]] = Field(default_factory=list)


class IdSearch(SimplenightModel):
    dining_id: str


class OpeningSearch(DiningBase, IdSearch):
    dining_id: str


class AdapterOpening(SimplenightModel):
    date: date
    times: List[str] = Field(default_factory=list)


class DiningDetail(SimplenightModel):
    dining_id: str
    name: str
    rating: float
    phone: str
    images: List[str] = Field(default_factory=list)
    location: BusinessLocation


class DiningUser(SimplenightModel):
    name: str
    image: str


class DiningReview(SimplenightModel):
    rating: float
    text: str
    timestamp: str
    user: DiningUser


class Customer(SimplenightModel):
    first_name: str
    last_name: str
    phone: str
    email: str


class DiningReservationRequest(DiningBase):
    customer: Customer
    user_id: str
    dining_id: str


class DiningReservation(SimplenightModel):
    note: str
    booking_id: str


class AdapterCancelRequest(SimplenightModel):
    booking_id: str
