from api.hotel.parsers.priceline_image_parser import PricelineImageParser
from api.management.commands.simplenight_base_command import SimplenightBaseCommand


class Command(SimplenightBaseCommand):
    def handle(self, *args, **options):
        PricelineImageParser().parse_and_save(pagination_limit=5000)
