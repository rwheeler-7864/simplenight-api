from django.test import TestCase

from api.tests import model_helper
from api.locations import airports


class TestAirports(TestCase):
    def test_find_by_prefix(self):
        model_helper.create_airport(airport_id=1, airport_code="FOO", airport_name="Foocity Intl")
        model_helper.create_airport(airport_id=2, airport_code="BAR", airport_name="Barland Commuter")
        model_helper.create_airport(airport_id=3, airport_code="BAZ", airport_name="Baztown International")
        model_helper.create_airport(airport_id=4, airport_code="BAX", airport_name="Baxville Airport")
        model_helper.create_airport(airport_id=5, airport_code="FOC", airport_name="Foo Town Commuter")

        matched_airports = airports.find_by_prefix("foo")
        self.assertEqual(2, len(matched_airports))
        self.assertEqual("Foocity Intl", matched_airports[0].airport_name)
        self.assertEqual("Foo Town Commuter", matched_airports[1].airport_name)

        matched_airports = airports.find_by_prefix("Ba")
        self.assertEqual(3, len(matched_airports))
        self.assertEqual("Barland Commuter", matched_airports[0].airport_name)
        self.assertEqual("Baztown International", matched_airports[1].airport_name)
        self.assertEqual("Baxville Airport", matched_airports[2].airport_name)

        matched_airports = airports.find_by_prefix("Bazt")
        self.assertEqual(1, len(matched_airports))

    def test_find_by_airport_code(self):
        model_helper.create_airport(airport_id=1, airport_code="FOO", airport_name="Foocity Intl")
        model_helper.create_airport(airport_id=2, airport_code="BAR", airport_name="Barland Commuter")
        model_helper.create_airport(airport_id=3, airport_code="BAZ", airport_name="Baztown International")

        matched_airport = airports.find_by_airport_code("BAR")
        self.assertEqual("Barland Commuter", matched_airport.airport_name)
