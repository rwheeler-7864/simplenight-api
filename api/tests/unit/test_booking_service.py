from datetime import date

from api.booking import booking_service
from api.hotel.models.adapter_models import AdapterHotel
from api.hotel.models.booking_model import HotelReservation, Locator
from api.hotel.models.hotel_api_model import HotelDetails, CancellationDetails, CancellationSummary
from api.hotel.models.hotel_common_models import RoomOccupancy
from api.models.models import PaymentTransaction
from api.tests import test_objects, model_helper
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestBookingService(SimplenightTestCase):
    def test_confirmation_email(self):
        room_type = test_objects.room_type()
        room_type.code = "room-type-123"
        room_type.name = "Test Room"

        room_rate = test_objects.room_rate(rate_key="rate-123", total="250.00")
        room_rate.room_type_code = "room-type-123"

        address = test_objects.address()
        checkin = date(2020, 1, 1)
        checkout = date(2020, 2, 1)
        hotel = AdapterHotel(
            provider="stub",
            hotel_id="100",
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            room_rates=[room_rate],
            room_types=[room_type],
            rate_plans=[],
            hotel_details=HotelDetails(name="Hotel Foo", address=address, hotel_code="SN123"),
        )

        provider = model_helper.create_provider("stub")
        model_helper.create_provider_hotel(provider=provider, provider_code="100", hotel_name="Test Hotel")

        customer = test_objects.customer("John", "Simplenight")
        traveler = test_objects.traveler("John", "Simplenight")

        reservation = HotelReservation(
            locator=Locator(id="123"),
            hotel_id="100",
            checkin=checkin,
            checkout=checkout,
            customer=customer,
            traveler=traveler,
            room_rate=room_rate,
            cancellation_details=[
                CancellationDetails(cancellation_type=CancellationSummary.NON_REFUNDABLE, description="Non-Refundable")
            ],
        )

        payment = PaymentTransaction(currency="USD")

        params = booking_service._generate_confirmation_email_params(hotel, reservation, payment, "recloc")
        self.assertEqual("recloc", params["booking_id"])
        self.assertEqual("$250.00", params["order_total"])
        self.assertEqual("Hotel Foo", params["hotel_name"])
        self.assertEqual("$250.00", params["hotel_sub_total"])
        self.assertEqual("123", params["record_locator"])
        self.assertEqual("Non-refundable", params["cancellation_policy"])
        self.assertEqual("123 Simple Way", params["hotel_address"])
        self.assertEqual("04:00pm", params["checkin"])
        self.assertEqual("12:00pm", params["checkout"])
        self.assertEqual("$0.00", params["resort_fee"])
        self.assertEqual("$37.50", params["hotel_taxes"])
        self.assertEqual("Test Room", params["hotel_room_type"])
        self.assertEqual("$212.50", params["order_base_rate"])
        self.assertEqual("$37.50", params["order_taxes"])
