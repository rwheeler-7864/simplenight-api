from datetime import datetime

from api.restaurants import restaurant_search
from api.multi.multi_product_models import RestaurantSearch
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestRestaurantSearch(SimplenightTestCase):
    def test_restaurant_search(self):
        reservation_time = datetime(2020, 1, 1, 7, 0)
        search = RestaurantSearch(location_id="123", reservation_date=reservation_time, party_size=4)

        restaurants = restaurant_search.search(search)
        self.assertGreater(len(restaurants), 1)
        self.assertIsNotNone(restaurants[0].restaurant_id)
        self.assertIsNotNone(restaurants[0].name)
        self.assertIsNotNone(restaurants[0].description)
        self.assertEqual(reservation_time.date(), restaurants[0].reservation_date)
        self.assertGreater(len(restaurants[0].reservation_times), 1)
