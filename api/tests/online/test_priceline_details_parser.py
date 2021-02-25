from django.test import TestCase

from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers.priceline_details_parser import PricelineDetailsParser


class TestPricelineDetailsParser(TestCase):
    def test_load_all_hotels(self):
        transport = PricelineTransport(test_mode=True, refid="10047")
        parser = PricelineDetailsParser(transport=transport)

        parser.load(limit=1000)