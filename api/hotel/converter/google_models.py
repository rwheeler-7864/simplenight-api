#######################################
#   Google Hotel Booking API Schema   #
#######################################

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import Field

from api.hotel.models.booking_model import Customer, PaymentMethod, CardType, Locator, SubmitErrorType
from api.common.common_models import SimplenightModel
from api.hotel.models.hotel_common_models import Address, Money, LineItemType
from api.hotel.models.hotel_api_model import GeoLocation, BedTypes, CancellationSummary


class ApiVersion(Enum):
    VERSION_1: 1


class DisplayString(SimplenightModel):
    text: str
    language: str


class BasicAmenities(SimplenightModel):
    free_breakfast: bool
    free_wifi: bool
    free_parking: bool


class GoogleImage(SimplenightModel):
    url: str
    description: DisplayString


class RoomCapacity(SimplenightModel):
    adults: int = 2
    children: Optional[int] = None


class GoogleRoomType(SimplenightModel):
    code: str
    name: DisplayString
    description: Optional[DisplayString]
    basic_amenities: BasicAmenities
    photos: List[GoogleImage]
    capacity: RoomCapacity
    bed_types: Optional[BedTypes] = None
    unstructured_policies: Optional[DisplayString] = None


# Room Occupancy, but Google-required format
# Children are specified as a list of integers representing child age
class RoomParty(SimplenightModel):
    children: List[int] = Field(default_factory=list)
    adults: int = 0


class GuaranteeType(Enum):
    NO_GUARANTEE = "NO_GUARANTEE"
    PAYMENT_CARD = "PAYMENT_CARD"


class GoogleCancellationPolicy(SimplenightModel):
    summary: CancellationSummary
    cancellation_deadline: str
    unstructured_policy: DisplayString


class GoogleRatePlan(SimplenightModel):
    code: str
    name: DisplayString
    description: DisplayString
    basic_amenities: BasicAmenities
    guarantee_type: GuaranteeType
    cancellation_policy: GoogleCancellationPolicy


class RoomRateLineItem(SimplenightModel):
    price: Money
    type: LineItemType
    paid_at_checkout: bool


class BaseGoogleRoomRate(SimplenightModel):
    code: str
    room_type_code: str
    rate_plan_code: str
    maximum_allowed_occupancy: RoomCapacity
    total_price_at_booking: Optional[Money]
    total_price_at_checkout: Optional[Money]
    partner_data: Optional[List[str]]


class GoogleRoomRate(BaseGoogleRoomRate):
    line_items: List[RoomRateLineItem]


class GoogleBookingRoomRate(BaseGoogleRoomRate):
    line_items: Optional[List[RoomRateLineItem]]


class GoogleHotelDetails(SimplenightModel):
    name: str
    address: Address
    geolocation: Optional[GeoLocation] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    photos: List[GoogleImage] = Field(default_factory=list)


class GoogleHotelApiResponse(SimplenightModel):
    api_version: int
    transaction_id: str
    hotel_id: str
    start_date: date
    end_date: date
    party: RoomParty
    room_types: List[GoogleRoomType]
    rate_plans: List[GoogleRatePlan]
    room_rates: List[GoogleRoomRate]
    hotel_details: GoogleHotelDetails


class GoogleHotelSearchRequest(SimplenightModel):
    api_version: int
    transaction_id: str
    hotel_id: str
    start_date: date
    end_date: date
    party: RoomParty
    language: str = "en"
    currency: str = "USD"


class GoogleTraveler(SimplenightModel):
    first_name: str
    last_name: str
    occupancy: RoomParty


class GooglePaymentCardParameters(SimplenightModel):
    card_type: CardType
    card_number: str
    cardholder_name: str
    expiration_month: str
    expiration_year: str
    cvc: str


class GooglePayment(SimplenightModel):
    type: PaymentMethod
    billing_address: Address
    payment_card_parameters: Optional[GooglePaymentCardParameters] = None
    payment_token: Optional[str] = None


class GoogleTracking(SimplenightModel):
    campaign_id: Optional[str]
    pos_url: Optional[str]


class GoogleSubmitError(SimplenightModel):
    type: SubmitErrorType
    message: str


class GoogleBookingSubmitRequest(SimplenightModel):
    api_version: int
    transaction_id: str
    hotel_id: str
    start_date: date
    end_date: date
    language: str
    customer: Customer
    traveler: GoogleTraveler
    room_rate: GoogleBookingRoomRate
    payment: Optional[GooglePayment] = None
    tracking: Optional[GoogleTracking] = None
    ip_address: Optional[str] = None


class GoogleStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class GoogleReservation(SimplenightModel):
    locator: Locator
    hotel_locators: List[Locator]
    hotel_id: str
    start_date: date
    end_date: date
    customer: Customer
    traveler: GoogleTraveler
    room_rate: GoogleBookingRoomRate


class GoogleBookingResponse(SimplenightModel):
    api_version: int
    transaction_id: str
    status: GoogleStatus
    reservation: GoogleReservation
