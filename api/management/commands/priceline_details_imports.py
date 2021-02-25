#!/usr/bin/env python

from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers.priceline_details_parser import PricelineDetailsParser
from api.management.commands.simplenight_base_command import SimplenightBaseCommand


class Command(SimplenightBaseCommand):
    def handle(self, *args, **options):
        PricelineDetailsParser.remove_old_data()

        for refid in ["10046", "10047"]:
            parser = PricelineDetailsParser(transport=PricelineTransport(test_mode=True, refid=refid))
            parser.load()
