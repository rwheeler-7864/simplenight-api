#!/usr/bin/env python

from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.parsers.hotelbeds_chains_parser import HotelbedsChainsParser
from api.management.commands.simplenight_base_command import SimplenightBaseCommand


class Command(SimplenightBaseCommand):
    def handle(self, *args, **options):
        HotelbedsChainsParser.remove_old_data()

        parser = HotelbedsChainsParser(transport=HotelbedsTransport(test_mode=True))
        parser.load()
