from django.core.management import BaseCommand

from api.hotel.parsers.priceline_city_parser import PricelineCityParser


class Command(BaseCommand):
    def handle(self, *args, **options):
        parser = PricelineCityParser()
        parser.parse()
