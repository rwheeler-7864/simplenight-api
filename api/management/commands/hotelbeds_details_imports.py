#!/usr/bin/env python

from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.parsers.hotelbeds_details_parser import HotelbedsDetailsParser
from api.management.commands.simplenight_base_command import SimplenightBaseCommand


class Command(SimplenightBaseCommand):
    def handle(self, *args, **options):
        # HotelbedsDetailsParser.remove_old_data()

        parser = HotelbedsDetailsParser(transport=HotelbedsTransport(test_mode=True))
        parser.load()
