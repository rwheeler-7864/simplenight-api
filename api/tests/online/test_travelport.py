import unittest
from datetime import datetime
from datetime import timedelta

from api.hotel.models.hotel_common_models import RoomOccupancy
from api.hotel.adapters.travelport.travelport import TravelportHotelAdapter
from api.hotel.models.hotel_api_model import HotelLocationSearch, HotelDetailsSearchRequest


class TestTravelport(unittest.TestCase):
    def _test_search(self):
        travelport = TravelportHotelAdapter()

        checkin_date = datetime.now().date() + timedelta(days=30)
        checkout_date = datetime.now().date() + timedelta(days=37)
        search_request = HotelLocationSearch(
            location_id="SFO",
            start_date=checkin_date,
            end_date=checkout_date,
            occupancy=RoomOccupancy(adults=1, children=2),
        )

        results = travelport.search_by_location(search_request)
        self.assertIsNotNone(results)

    def _test_hotel_details(self):
        travelport = TravelportHotelAdapter()
        hotel_details = HotelDetailsSearchRequest(
            chain_code="HY",
            hotel_code="09974",
            start_date=datetime.now().date() + timedelta(days=30),
            end_date=datetime.now().date() + timedelta(days=37),
        )

        response = travelport.details(hotel_details)
        self.assertIsNotNone(response)
