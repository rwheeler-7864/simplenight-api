import uuid
from datetime import date

from api.hotel.models.booking_model import (
    Customer,
    Traveler,
    PaymentCardParameters,
    CardType,
    Payment,
    HotelBookingRequest,
)
from api.hotel import provider_cache_service
from api.hotel.adapters.stub.stub import StubHotelAdapter
from api.hotel.models.hotel_common_models import RoomOccupancy, Address
from api.hotel.models.adapter_models import AdapterHotelSearch, AdapterOccupancy
from api.tests import test_objects
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestStubHotelAdapter(SimplenightTestCase):
    def test_search_by_hotel_id(self):
        search_request = AdapterHotelSearch(
            provider_hotel_id="A1H2J6",
            simplenight_hotel_id="SN123",
            start_date=date(2020, 1, 20),
            end_date=date(2020, 1, 27),
            occupancy=AdapterOccupancy(adults=2, children=1),
        )

        stub_adapter = StubHotelAdapter()
        response = stub_adapter.search_by_id(search_request)

        self.assertIsNotNone(response.hotel_id)
        self.assertIsNotNone(response.start_date)
        self.assertIsNotNone(response.start_date)
        self.assertIsNotNone(response.occupancy)
        self.assertIsNotNone(response.room_types)
        self.assertIsNotNone(response.room_types[0].bed_types)
        self.assertIsNotNone(response.room_types[0].amenities)
        self.assertIsNotNone(response.room_types[0].photos)

        self.assertIsNotNone(response.room_rates[0])
        self.assertIsNotNone(response.room_rates[0].total)
        self.assertIsNotNone(response.room_rates[0].total_tax_rate)
        self.assertIsNotNone(response.room_rates[0].total_base_rate)

    def test_booking(self):
        customer = Customer(
            first_name="John",
            last_name="Smith",
            phone_number="+1 (555) 867-5309",
            email="john.smith@gmail.com",
            country="US",
        )

        traveler = Traveler(first_name="Jane", last_name="Smith", occupancy=RoomOccupancy(adults=1, children=0))
        provider_room_rate = test_objects.room_rate(
            rate_key="rate-key", base_rate="526.22", total="589.51", tax_rate="63.29"
        )
        simplenight_room_rate = test_objects.room_rate(
            rate_key="sn-rate-key", base_rate="526.22", total="589.51", tax_rate="63.29"
        )

        payment_card_params = PaymentCardParameters(
            card_type=CardType.VI,
            card_number="4111111111111111",
            cardholder_name="John Q. Smith",
            expiration_month="05",
            expiration_year="25",
            cvv="123",
        )

        address = Address(
            city="San Francisco", province="CA", postal_code="94111", country="US", address1="120 Market Street"
        )

        payment = Payment(billing_address=address, payment_card_parameters=payment_card_params)

        booking_request = HotelBookingRequest(
            api_version=1,
            transaction_id=str(uuid.uuid4()),
            hotel_id="HAUE1X",
            language="en_US",
            customer=customer,
            traveler=traveler,
            room_code=provider_room_rate.code,
            payment=payment,
        )

        adapter_hotel = test_objects.hotel()
        adapter_hotel.hotel_id = "HAUE1X"
        provider_cache_service.save_provider_rate(adapter_hotel, provider_room_rate, simplenight_room_rate)

        stub_adapter = StubHotelAdapter()
        reservation = stub_adapter.book(booking_request)

        self.assertIsNotNone(reservation)
        self.assertIsNotNone(reservation.locator.id)
        self.assertIsNotNone(reservation.hotel_locator[0].id)
        self.assertIsNotNone(reservation.hotel_id)
        self.assertEqual("2020-01-01", str(reservation.checkin))
        self.assertEqual("2020-02-01", str(reservation.checkout))
        self.assertEqual("John", reservation.customer.first_name)
        self.assertEqual("Smith", reservation.customer.last_name)
        self.assertEqual("+1 (555) 867-5309", reservation.customer.phone_number)
        self.assertIsNotNone("john.smith@gmail.com", reservation.customer.email)
        self.assertEqual("Jane", reservation.traveler.first_name)
        self.assertEqual("Smith", reservation.traveler.last_name)
        self.assertEqual(1, reservation.traveler.occupancy.adults)
        self.assertEqual("526.22", str(reservation.room_rate.total_base_rate.amount))
        self.assertEqual("63.29", str(reservation.room_rate.total_tax_rate.amount))
        self.assertEqual("589.51", str(reservation.room_rate.total.amount))
