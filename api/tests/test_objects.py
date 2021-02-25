import decimal
import uuid
from datetime import date, timedelta, datetime

from api.hotel.models.adapter_models import AdapterLocationSearch, AdapterOccupancy, AdapterHotelSearch
from api.hotel.models.booking_model import (
    Customer,
    Traveler,
    Payment,
    PaymentCardParameters,
    CardType,
    PaymentMethod,
    HotelBookingRequest,
)
from api.hotel.models.hotel_api_model import (
    AdapterHotel,
    RoomType,
    HotelSpecificSearch,
    HotelDetails,
    SimplenightHotel,
    SimplenightRoomType,
    CancellationSummary,
    CancellationPolicy,
)
from api.hotel.models.hotel_common_models import RoomOccupancy, Address, RateType, RoomRate, Money
from api.tests import to_money


def hotel(room_rates=None):
    if room_rates is None:
        room_rates = []

    return AdapterHotel(
        provider="stub_hotel",
        hotel_id="100",
        start_date=date(2020, 1, 1),
        end_date=date(2020, 2, 1),
        occupancy=RoomOccupancy(adults=1),
        room_rates=room_rates,
        room_types=[],
        rate_plans=[],
        hotel_details=HotelDetails(name="Hotel Foo", address=address(), hotel_code="SN123"),
    )


def simplenight_hotel(hotel_id="1"):
    return SimplenightHotel(
        hotel_id=hotel_id,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 2),
        occupancy=RoomOccupancy(adults=1),
        room_types=[
            SimplenightRoomType(
                code="foo_1",
                name="Foo_1",
                amenities=[],
                photos=[],
                capacity=RoomOccupancy(adults=1),
                total_base_rate=Money(amount=decimal.Decimal("80"), currency="USD"),
                total_tax_rate=Money(amount=decimal.Decimal("20"), currency="USD"),
                total=Money(amount=decimal.Decimal("100"), currency="USD"),
                avg_nightly_rate=Money(amount=decimal.Decimal("100"), currency="USD"),
                cancellation_policy=CancellationPolicy(summary=CancellationSummary.NON_REFUNDABLE),
                rate_type=RateType.BOOKABLE,
            )
        ],
    )


def room_rate(rate_key: str, total, base_rate=None, tax_rate=None):
    if isinstance(total, str):
        total = to_money(total)

    if base_rate is None:
        base_rate = total.amount * decimal.Decimal("0.85")

    if tax_rate is None:
        tax_rate = total.amount * decimal.Decimal("0.15")

    return RoomRate(
        code=rate_key,
        rate_plan_code="foo",
        room_type_code="foo",
        rate_type=RateType.BOOKABLE,
        total_base_rate=to_money(base_rate),
        total_tax_rate=to_money(tax_rate),
        total=total,
        maximum_allowed_occupancy=RoomOccupancy(adults=2),
    )


def room_type():
    return RoomType(
        code=str(uuid.uuid4),
        name=f"Test Rate {str(uuid.uuid4())[:4]}",
        description="Test Description",
        amenities=[],
        photos=[],
        capacity=RoomOccupancy(adults=2),
        bed_types=None,
    )


def customer(first_name="John", last_name="Simplenight"):
    return Customer(
        first_name=first_name,
        last_name=last_name,
        phone_number="5558675309",
        email="john.simp@simplenight.com",
        country="US",
    )


def address():
    return Address(address1="123 Market St", city="San Francisco", province="CA", country="US", postal_code="94111")


def traveler(first_name="John", last_name="Simplenight"):
    return Traveler(first_name=first_name, last_name=last_name, occupancy=RoomOccupancy(adults=1, children=0))


def payment(card_number=None):
    if card_number is None:
        card_number = "4242424242424242"

    exp_date = datetime.now().date() + timedelta(days=365)
    return Payment(
        billing_address=address(),
        payment_method=PaymentMethod.PAYMENT_CARD,
        payment_card_parameters=PaymentCardParameters(
            card_type=CardType.VI,
            card_number=card_number,
            cardholder_name="John Q. Simplenight",
            expiration_month=str(exp_date.month),
            expiration_year=str(exp_date.year),
            cvv="123",
        ),
    )


def booking_request(payment_obj=None, rate_code=None):
    if payment_obj is None:
        payment_obj = payment(card_number="4242424242424242")

    if rate_code is None:
        rate_code = "rate_key"

    return HotelBookingRequest(
        api_version=1,
        transaction_id=str(uuid.uuid4())[:8],
        hotel_id="1",
        language="en_US",
        customer=customer(),
        traveler=traveler(),
        room_code=rate_code,
        payment=payment_obj,
    )


def hotel_specific_search(start_date=None, end_date=None, hotel_id="123", provider="stub_hotel"):
    if start_date is None:
        start_date = date(2020, 1, 1)

    if end_date is None:
        end_date = date(2020, 1, 7)

    return HotelSpecificSearch(
        start_date=start_date, end_date=end_date, occupancy=RoomOccupancy(), hotel_id=hotel_id, provider=provider
    )


def adapter_hotel_search(start_date=None, end_date=None, hotel_id="123", adapter="stub_hotel"):
    if start_date is None:
        start_date = date(2020, 1, 1)

    if end_date is None:
        end_date = date(2020, 1, 7)

    return AdapterHotelSearch(
        start_date=start_date,
        end_date=end_date,
        occupancy=AdapterOccupancy(),
        simplenight_hotel_id=hotel_id,
        provider_hotel_id="123",
    )


def adapter_location_search(start_date=None, end_date=None, location_id="123"):
    if start_date is None:
        start_date = date(2020, 1, 1)

    if end_date is None:
        end_date = date(2020, 1, 7)

    return AdapterLocationSearch(
        start_date=start_date,
        end_date=end_date,
        occupancy=AdapterOccupancy(),
        location_id=location_id,
    )
