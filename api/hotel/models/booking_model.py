from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from pydantic import Field

from api.common.common_models import SimplenightModel
from api.hotel.models.hotel_api_model import CancellationDetails
from api.hotel.models.hotel_common_models import RoomOccupancy, Address, RoomRate


class SubmitErrorType(Enum):
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    API_VERSION_UNSUPPORTED = "API_VERSION_UNSUPPORTED"
    CHECKIN_TOO_CLOSE = "CHECKIN_TOO_CLOSE"
    CUSTOMER_NAME_INVALID = "CUSTOMER_NAME_INVALID"
    DATE_SELECTION_INVALID = "DATE_SELECTION_INVALID"
    DUPLICATE_BOOKING = "DUPLICATE_BOOKING"
    HOTEL_NOT_FOUND = "HOTEL_NOT_FOUND"
    NETWORK_ERROR = "NETWORK_ERROR"
    PAYMENT_BILLING_ADDRESS_INVALID = "PAYMENT_BILLING_ADDRESS_INVALID"
    PAYMENT_CARD_CARDHOLDER_NAME_INVALID = "PAYMENT_CARD_CARDHOLDER_NAME_INVALID"
    PAYMENT_CARD_CVC_INVALID = "PAYMENT_CARD_CVC_INVALID"
    PAYMENT_CARD_EXPIRATION_INVALID = "PAYMENT_CARD_EXPIRATION_INVALID"
    PAYMENT_CARD_NUMBER_INVALID = "PAYMENT_CARD_NUMBER_INVALID"
    PAYMENT_CARD_TYPE_NOT_SUPPORTED = "PAYMENT_CARD_TYPE_NOT_SUPPORTED"
    PAYMENT_DECLINED = "PAYMENT_DECLINED"
    PAYMENT_INVALID = "PAYMENT_INVALID"
    PAYMENT_INSUFFICIENT = "PAYMENT_INSUFFICIENT"
    PAYMENT_PROCESSOR_ERROR = "PAYMENT_PROCESSOR_ERROR"
    PAYMENT_TYPE_NOT_ACCEPTED = "PAYMENT_TYPE_NOT_ACCEPTED"
    RATE_PLAN_UNAVAILABLE = "RATE_PLAN_UNAVAILABLE"
    RECOVERABLE_ERROR = "RECOVERABLE_ERROR"
    REQUEST_DATA_INVALID = "REQUEST_DATA_INVALID"
    REQUEST_INCOMPLETE = "REQUEST_INCOMPLETE"
    REQUEST_NOT_PARSABLE = "REQUEST_NOT_PARSABLE"
    ROOM_RATE_MISMATCH = "ROOM_RATE_MISMATCH"
    ROOM_RATE_PRICE_MISMATCH = "ROOM_RATE_PRICE_MISMATCH"
    ROOM_RATE_UNAVAILABLE = "ROOM_RATE_UNAVAILABLE"
    ROOM_TYPE_UNAVAILABLE = "ROOM_TYPE_UNAVAILABLE"
    TRAVELER_NAME_INVALID = "TRAVELER_NAME_INVALID"
    SUPPLIER_ERROR = "SUPPLIER_ERROR"


class Customer(SimplenightModel):
    first_name: str
    last_name: str
    phone_number: str
    email: str
    country: str


class Traveler(SimplenightModel):
    first_name: str
    last_name: str
    occupancy: RoomOccupancy


class CardType(Enum):
    AX = "AX"
    DC = "DC"
    DS = "DS"
    JC = "JC"
    MC = "MC"
    VI = "VI"


class PaymentMethod(Enum):
    PAYMENT_TOKEN = "PAYMENT_TOKEN"
    CREDIT_CARD = "CREDIT_CARD"
    PAYMENT_CARD = "PAYMENT_CARD"


class PaymentCardParameters(SimplenightModel):
    card_type: CardType
    card_number: str
    cardholder_name: str
    expiration_month: str
    expiration_year: str
    cvv: str


class Payment(SimplenightModel):
    billing_address: Optional[Address]
    payment_card_parameters: Optional[PaymentCardParameters] = None
    payment_token: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None


class HotelBookingRequest(SimplenightModel):
    api_version: int
    transaction_id: str
    hotel_id: str
    room_code: str
    language: str
    customer: Customer
    traveler: Traveler
    payment: Optional[Payment] = None


class AdapterHotelBookingRequest(SimplenightModel):
    transaction_id: str
    hotel_id: str
    room_code: str
    language: str
    customer: Customer
    traveler: Traveler


class MultiProductHotelBookingRequest(SimplenightModel):
    hotel_id: str
    room_code: str
    traveler: Traveler


class Status(SimplenightModel):
    success: bool
    message: str


class Locator(SimplenightModel):
    id: str
    pin: Optional[str] = None


class HotelReservation(SimplenightModel):
    locator: Locator
    hotel_locator: Optional[List[Locator]]
    hotel_id: str
    checkin: date
    checkout: date
    customer: Customer
    traveler: Traveler
    room_rate: RoomRate
    cancellation_details: List[CancellationDetails] = Field(default_factory=list)


class HotelBookingResponse(SimplenightModel):
    api_version: int
    transaction_id: str
    booking_id: str
    status: Status
    reservation: HotelReservation


class HotelPriceVerificationHolder(SimplenightModel):
    original_room_rates: List[RoomRate]
    verified_room_rates: List[RoomRate]


class AdapterActivityBookingItem(SimplenightModel):
    code: str
    quantity: int
    price: Optional[Decimal]


class ActivityBookingItem(SimplenightModel):
    code: str
    quantity: int


class ActivityBookingRequest(SimplenightModel):
    code: str
    language_code: str
    activity_date: date
    activity_time: time
    currency: str
    notes: Optional[str]
    data: Optional[str]
    misc: Optional[str]
    supplier_date: Optional[str]
    items: List[ActivityBookingItem]


class ActivityReservation(SimplenightModel):
    status: Status
    record_locator: Locator
    items: List[ActivityBookingItem]


class AdapterActivityBookingRequest(SimplenightModel):
    code: str
    language_code: str
    activity_date: date
    activity_time: time
    currency: str
    notes: Optional[str]
    data: Optional[str]
    misc: Optional[str]
    supplier_date: Optional[str]
    items: List[AdapterActivityBookingItem]


class AdapterActivityBookingResponse(SimplenightModel):
    status: Status
    record_locator: Locator


class MultiProductBookingRequest(SimplenightModel):
    api_version: int
    transaction_id: str
    language: str
    customer: Customer
    payment: Payment
    hotel_booking: Optional[MultiProductHotelBookingRequest]
    activity_booking: Optional[ActivityBookingRequest]


class MultiProductBookingResponse(SimplenightModel):
    api_version: int
    transaction_id: str
    status: Status
    booking_id: str
    hotel_reservation: Optional[HotelReservation]
    activity_reservation: Optional[ActivityReservation]
