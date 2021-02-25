from unittest.mock import Mock

from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.tests import test_objects
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestPricelineUnit(SimplenightTestCase):
    def test_room_details_map(self):
        """
        Room Details Map executes room details in a thread pool
        Test that results are returned in a map keyed by room code
        """

        priceline = PricelineAdapter(transport=Mock())
        priceline.room_details = lambda x: f"result_{x}"
        adapter_hotel = test_objects.hotel()
        room_rate1 = test_objects.room_rate(rate_key="one", total="100")
        room_rate2 = test_objects.room_rate(rate_key="two", total="100")
        adapter_hotel.room_rates.extend([room_rate1, room_rate2])

        room_details_map = priceline._room_details_map(adapter_hotel)

        self.assertEqual(2, len(room_details_map))
        self.assertEqual("result_one", room_details_map["one"])
        self.assertEqual("result_two", room_details_map["two"])