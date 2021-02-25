#!/usr/bin/env python
from django.core.management import BaseCommand

from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers.priceline_chains_parser import PricelineHotelChainsParser


class Command(BaseCommand):
    def handle(self, *args, **options):
        parser = PricelineHotelChainsParser(PricelineTransport(test_mode=True))

        parser.remove_old_data()
        parser.execute()
