from django.core.management import BaseCommand

from api.locations.geonames import GeonamesParser, GeonameSettings


class Command(BaseCommand):
    def handle(self, *args, **options):
        parser = GeonamesParser(config=GeonameSettings())
        parser.download_and_parse()
