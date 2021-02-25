from datetime import datetime, date

from api.multi import multi_product
from api.multi.multi_product_models import SearchRequest, Products, ActivitySpecificSearch, RestaurantSearch
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestSearch(SimplenightTestCase):
    def test_search_restaurants_and_activities(self):
        search_date = datetime(2020, 1, 1, 19, 0)
        request = SearchRequest(
            product_types=[Products.DINING, Products.ACTIVITIES],
            restaurant_search=RestaurantSearch(location_id="123", reservation_date=search_date, party_size=4),
            activity_search=ActivitySpecificSearch(
                begin_date=search_date.date(), end_date=date(2020, 1, 5), adults=1, children=0, activity_id="123"
            ),
        )

        results = multi_product.search_request(request)
        print(results)
