import random
from datetime import datetime, timedelta
from unittest.mock import patch

from api.hotel import hotel_service, provider_cache_service
from api.booking import booking_service
from api.hotel.adapters.hotelbeds.hotelbeds_adapter import HotelbedsAdapter
from api.hotel.models.adapter_models import AdapterLocationSearch, AdapterOccupancy
from api.hotel.models.hotel_api_model import HotelLocationSearch
from api.hotel.models.hotel_common_models import RoomOccupancy, RateType
from api.models.models import HotelBooking
from api.tests import test_objects
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestHotelBedsOnline(SimplenightTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.hotelbeds = HotelbedsAdapter()

    def test_location_search(self):
        search_request = self.create_location_search()
        response = self.hotelbeds.search_by_location(search_request)
        print(response)

    def test_location_recheck(self):
        search_request = self.create_location_search()
        response = self.hotelbeds.search_by_location(search_request)

        self.assertTrue(len(response) >= 1)

        room_rate_to_check = response[0].room_rates[0]
        room_rate_verified = self.hotelbeds.recheck(room_rate_to_check)

        print(room_rate_to_check)
        print(room_rate_verified)

    def test_location_search_bad_location(self):
        search_request = self.create_location_search(location_name="XXX")
        response = self.hotelbeds.search_by_location(search_request)
        assert len(response) == 0

    def test_hotel_details(self):
        hotel_codes = ["123456", "654321"]
        self.hotelbeds.details(hotel_codes, "en_US")

    def test_hotelbeds_booking(self):
        checkin = datetime.now().date() + timedelta(days=30)
        checkout = datetime.now().date() + timedelta(days=35)
        search = HotelLocationSearch(
            start_date=checkin,
            end_date=checkout,
            occupancy=RoomOccupancy(adults=1),
            location_id="SFO",
            provider="hotelbeds",
        )

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            availability_response = hotel_service.search_by_location(search)

        # Find first hotel with a bookable rate
        all_rooms = [room for hotel in availability_response for room in hotel.room_types]
        bookable_rooms = [room for room in all_rooms if room.rate_type == RateType.BOOKABLE]
        room_to_book = random.choice(bookable_rooms)

        self.assertIsNotNone(bookable_rooms)

        booking_request = test_objects.booking_request(rate_code=room_to_book.code)
        booking_response = booking_service.book_hotel(booking_request)

        saved_room_data = provider_cache_service.get_cached_room_data(room_to_book.code)
        assert booking_response.reservation.room_rate.code == saved_room_data.simplenight_rate.code

        hotel_booking = HotelBooking.objects.filter(record_locator=booking_response.reservation.locator.id).first()
        assert hotel_booking.provider_total == saved_room_data.provider_rate.total.amount
        assert hotel_booking.total_price == room_to_book.total.amount

    def test_hotelbeds_facilities_types(self):
        response = self.hotelbeds.get_facilities_types()
        self.assertTrue(len(response) > 0)

    def test_hotelbeds_categories(self):
        response = self.hotelbeds.get_categories()
        print(response)

    @staticmethod
    def create_location_search(location_name="TVL", checkin=None, checkout=None):
        if checkin is None:
            checkin = datetime.now().date() + timedelta(days=30)

        if checkout is None:
            checkout = datetime.now().date() + timedelta(days=35)

        search_request = AdapterLocationSearch(
            location_id=location_name, start_date=checkin, end_date=checkout, occupancy=AdapterOccupancy(),
        )

        return search_request
