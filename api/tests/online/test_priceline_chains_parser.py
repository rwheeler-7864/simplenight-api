from django.test import TestCase

from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers.priceline_chains_parser import PricelineHotelChainsParser
from api.models.models import ProviderChain


class TestPricelineHotelChainsParser(TestCase):
    def test_load_hotel_chains(self):
        transport = PricelineTransport(test_mode=True)
        parser = PricelineHotelChainsParser(transport=transport)
        parser.execute(limit=50, chunk_size=25)

        chain_mapping = ProviderChain.objects.all()
        self.assertEqual(50, len(chain_mapping))

        parser.remove_old_data()
        chain_mapping = ProviderChain.objects.all()
        self.assertEqual(0, len(chain_mapping))
