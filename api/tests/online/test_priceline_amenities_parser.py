from django.test import TestCase

from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers.priceline_amenities_parser import PricelineAmenitiesParser


class TestPricelineAmenitiesParser(TestCase):
    def test_load_amenities(self):
        parser = PricelineAmenitiesParser(PricelineTransport(test_mode=True))
        parser.execute()
