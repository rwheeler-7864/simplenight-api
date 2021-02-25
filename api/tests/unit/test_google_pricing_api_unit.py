import unittest
from datetime import date

from lxml import etree

from api.hotel.google_pricing import google_pricing_serializer
from api.tests import test_objects
from api.tests.utils import load_test_resource


class TestGooglePricingApiUnit(unittest.TestCase):
    def test_deserialize_live_pricing(self):
        resource = load_test_resource("google-pricing-api/query.xml")
        response = google_pricing_serializer.deserialize(resource)

        self.assertEqual(date(2020, 12, 29), response.checkin)
        self.assertEqual(1, response.nights)
        self.assertEqual(["RA-F8738", "ON-F8692", "MX-58244"], response.hotel_codes)

    def test_serialize_live_pricing(self):
        resource = load_test_resource("google-pricing-api/query.xml")
        query = google_pricing_serializer.deserialize(resource)

        hotel_one = test_objects.simplenight_hotel(hotel_id="1")
        hotel_two = test_objects.simplenight_hotel(hotel_id="2")

        result = google_pricing_serializer.serialize(query, [hotel_one, hotel_two])

        parsed_result = etree.fromstring(result)

        self.assertEqual(2, len(parsed_result.findall(".//Result")))
