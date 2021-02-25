import decimal
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import Field

from api.common.common_models import SimplenightModel
from api.hotel.models.hotel_common_models import (
    RoomOccupancy,
    Address,
    RateType,
    Money,
    DailyRate,
    PostpaidFees,
    RoomRate,
    BookingStatus,
)


class SimplenightAmenities(Enum):
    POOL = "Pool"
    FREE_PARKING = "Free Parking"
    PARKING = "Parking"
    BREAKFAST = "Breakfast"
    WIFI = "Free Wi-Fi"
    AIRPORT_SHUTTLE = "Free Airport Shuttle"
    KITCHEN = "Kitchen"
    PET_FRIENDLY = "Pet Friendly"
    AIR_CONDITIONING = "Air Conditioned"
    CASINO = "Casino"
    WATER_PARK = "Water Park"
    ALL_INCLUSIVE = "All Inclusive"
    SPA = "Spa"
    WASHER_DRYER = "Washer and Dryer"
    LAUNDRY_SERVICES = "Laundry Services"
    HOT_TUB = "Hot Tub"
    BAR = "Bar"
    MINIBAR = "Mini Bar"
    GYM = "Health Club or Gym"
    RESTAURANT = "Restaurant"
    SAUNA = "Sauna"

    @classmethod
    def from_value(cls, value):
        if not hasattr(cls, "value_map"):
            cls.value_map = {x.value: x for x in SimplenightAmenities}

        return cls.value_map[value]


class HotelSearch(SimplenightModel):
    start_date: date
    end_date: date
    occupancy: Optional[RoomOccupancy]
    daily_rates: bool = False
    language: Optional[str] = "en"
    currency: Optional[str] = "USD"
    checkin_time: Optional[Union[str, datetime]] = None
    checkout_time: Optional[Union[str, datetime]] = None
    provider: Optional[str] = None


class HotelLocationSearch(HotelSearch):
    location_id: str


class HotelSpecificSearch(HotelSearch):
    hotel_id: str


class HotelBatchSearch(HotelSearch):
    hotel_ids: List[str] = Field(default_factory=list)


class HotelDetailsSearchRequest(SimplenightModel):
    hotel_code: str
    start_date: date
    end_date: date
    num_rooms: int = 1
    currency: str = "USD"
    language: str = "en_US"
    provider: str = "stub_hotel"
    chain_code: Optional[str] = None


class ImageType(Enum):
    EXTERIOR = "Exterior"
    ROOM = "Room"
    UNKNOWN = ""


class Image(SimplenightModel):
    url: str
    type: Optional[ImageType]
    display_order: Optional[int] = None


class BedTypes(SimplenightModel):
    total: int = 0
    king: int = 0
    queen: int = 0
    double: int = 0
    single: int = 0
    sofa: int = 0
    murphy: int = 0
    bunk: int = 0
    other: int = 0


class RoomType(SimplenightModel):
    code: str
    name: str
    description: Optional[str]
    amenities: List[SimplenightAmenities]
    photos: List[Image]
    capacity: RoomOccupancy
    bed_types: Optional[BedTypes]
    unstructured_policies: Optional[str] = None
    avg_nightly_rate: Optional[Money] = None


class CancellationSummary(Enum):
    UNKNOWN_CANCELLATION_POLICY = "UNKNOWN_CANCELLATION_POLICY"
    FREE_CANCELLATION = "FREE_CANCELLATION"
    NON_REFUNDABLE = "NON_REFUNDABLE"
    PARTIAL_REFUND = "PARTIAL_REFUND"

    @classmethod
    def from_value(cls, value):
        if not hasattr(cls, "value_map"):
            cls.value_map = {x.value: x for x in CancellationSummary}

        return cls.value_map[value]


class CancellationPolicy(SimplenightModel):
    summary: CancellationSummary
    cancellation_deadline: Optional[date] = None
    unstructured_policy: Optional[str] = None


class CancellationDetails(SimplenightModel):
    cancellation_type: CancellationSummary
    description: str
    begin_date: Optional[date] = None
    end_date: Optional[date] = None
    penalty_amount: Optional[decimal.Decimal] = None
    penalty_currency: Optional[str] = None
    refund_amount: Optional[decimal.Decimal] = None
    refund_currency: Optional[str] = None


class RatePlan(SimplenightModel):
    code: str
    name: str
    description: str
    amenities: List[SimplenightAmenities]
    cancellation_policy: CancellationPolicy


class GeoLocation(SimplenightModel):
    latitude: float
    longitude: float


class HotelDetails(SimplenightModel):
    name: str
    address: Address
    hotel_code: str
    checkin_time: Optional[str]
    checkout_time: Optional[str]
    photos: List[Image] = Field(default_factory=list)
    amenities: Optional[List[SimplenightAmenities]] = Field(default_factory=list)
    thumbnail_url: str = None
    geolocation: Optional[GeoLocation] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    homepage_url: Optional[str] = None
    chain_code: Optional[str] = None
    chain_name: Optional[str] = None
    star_rating: Optional[float] = None
    review_rating: Optional[float] = None
    property_description: Optional[str] = None


class ErrorResponse(SimplenightModel):
    type: str
    message: str


class AdapterHotel(SimplenightModel):
    provider: str
    hotel_id: str
    start_date: date
    end_date: date
    occupancy: RoomOccupancy
    room_types: List[RoomType]
    rate_plans: Optional[List[RatePlan]] = None
    room_rates: Optional[List[RoomRate]] = None
    hotel_details: Optional[HotelDetails] = None
    error: Optional[ErrorResponse] = None


class SimplenightRoomType(SimplenightModel):
    """
    Defines an API model for Simplenight's Front End API.
    This differs from the models returned by adapters, and the models returned in the Google API
    In this model, room types, rate plans, and rates are combined into a simple list
    """

    code: str
    name: str
    description: Optional[str]
    amenities: List[SimplenightAmenities]
    photos: List[Image]
    capacity: RoomOccupancy
    bed_types: Optional[BedTypes]
    total_base_rate: Money
    total_tax_rate: Money
    total: Money
    rate_type: RateType
    avg_nightly_rate: Money
    cancellation_policy: CancellationPolicy
    daily_rates: Optional[List[DailyRate]] = None
    unstructured_policies: Optional[str] = None
    postpaid_fees: Optional[PostpaidFees] = None


class Hotel(SimplenightModel):
    hotel_id: str
    start_date: date
    end_date: date
    occupancy: RoomOccupancy
    hotel_details: Optional[HotelDetails]
    room_types: Optional[List[RoomType]] = None
    room_rates: Optional[List[RoomRate]] = None
    rate_plans: Optional[List[RatePlan]] = None
    average_nightly_rate: decimal.Decimal = None
    average_nightly_base: decimal.Decimal = None
    average_nightly_tax: decimal.Decimal = None
    error: Optional[ErrorResponse] = None


class SimplenightHotel(SimplenightModel):
    hotel_id: str
    start_date: date
    end_date: date
    hotel_details: Optional[HotelDetails]
    occupancy: RoomOccupancy
    room_types: Optional[List[SimplenightRoomType]] = None
    avg_nightly_rate: decimal.Decimal = None
    avg_nightly_base: decimal.Decimal = None
    avg_nightly_tax: decimal.Decimal = None
    error: Optional[ErrorResponse] = None


class SimplenightHotelList(SimplenightModel):
    __root__: List[SimplenightHotel]


class HotelPriceVerification(SimplenightModel):
    is_allowed_change: bool
    is_exact_price: bool
    verified_room_rate: RoomRate
    original_total: decimal.Decimal
    recheck_total: decimal.Decimal
    price_difference: decimal.Decimal


class RoomDataCachePayload(SimplenightModel):
    hotel_id: str
    adapter_hotel: AdapterHotel
    provider: str
    checkin: date
    checkout: date
    room_code: str
    provider_rate: RoomRate
    simplenight_rate: RoomRate


class ItineraryItem(SimplenightModel):
    name: str
    price: Money
    confirmation: str


class HotelItineraryItem(ItineraryItem):
    start_date: date
    end_date: date
    address: Address


class CancelRequest(SimplenightModel):
    booking_id: str
    last_name: str


class CancelResponse(SimplenightModel):
    is_cancellable: bool
    booking_status: BookingStatus
    itinerary: HotelItineraryItem
    details: CancellationDetails


class CancelConfirmResponse(SimplenightModel):
    booking_id: str
    record_locator: str
    booking_status: BookingStatus
    cancelled: bool
    amount_refunded: decimal.Decimal
