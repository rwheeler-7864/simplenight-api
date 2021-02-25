from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch

from api.common.common_models import from_json
from api.hotel.models.hotel_api_model import HotelSpecificSearch
from api.hotel.models.hotel_common_models import RoomOccupancy
from api.locations.models import Location, LocationType
from api.multi.multi_product_models import (
    ActivityLocationSearch,
    SearchRequest,
    SearchResponse,
    Products,
    RestaurantSearch,
)
from api.tests.unit.simplenight_test_case import SimplenightTestCase

SEARCH_BY_ID = "/api/v1/multi/search"


class TestSearchViews(SimplenightTestCase):
    def test_activity_search(self):
        activity_search = ActivityLocationSearch(
            begin_date=datetime.now(), end_date=datetime.now(), adults=1, children=0, location_id="123"
        )

        search_request = SearchRequest(product_types=[Products.ACTIVITIES], activity_search=activity_search)
        print(search_request.json())

        with patch("api.locations.location_service.find_city_by_simplenight_id") as mock_find_city:
            mock_find_city.return_value = self._get_test_city()
            response = self._post(SEARCH_BY_ID, search_request)

        results = from_json(response.content, SearchResponse)
        self.assertGreater(len(results.activity_results), 1)
        self.assertIsNotNone(results.activity_results[0].name)

    def test_hotel_and_restaurant_search(self):
        checkin = date(2020, 1, 1)
        checkout = date(2020, 1, 2)
        occupancy = RoomOccupancy(adults=1)
        hotel_search = HotelSpecificSearch(start_date=checkin, end_date=checkout, hotel_id="123", occupancy=occupancy)

        reservation_time = datetime(2020, 1, 1, 19, 1)
        restaurant_search = RestaurantSearch(location_id="123", reservation_date=reservation_time, party_size=2)

        search_request = SearchRequest(
            product_types=[Products.HOTELS, Products.DINING],
            hotel_search=hotel_search,
            restaurant_search=restaurant_search,
        )

        print(search_request.json())

        with patch("api.hotel.hotel_mappings.find_simplenight_hotel_id") as mock_find_simplenight_id:
            mock_find_simplenight_id.return_value = "123"
            with patch("api.hotel.hotel_mappings.find_provider_hotel_id") as mock_find_provider:
                mock_find_provider.return_value = "ABC123"
                response = self._post(SEARCH_BY_ID, search_request)

        results = from_json(response.content, SearchResponse)
        print(results)

    def _post(self, endpoint, data):
        return self.client.post(path=endpoint, data=data.json(), format="json")

    @staticmethod
    def _get_test_city():
        return Location(
            location_id="123",
            language_code="en",
            location_name="Testville",
            iso_country_code="XX",
            latitude=Decimal("10.0"),
            longitude=Decimal("20.0"),
            location_type=LocationType.CITY,
        )
