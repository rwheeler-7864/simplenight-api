from django.core.management import BaseCommand

from api.locations import airports


class Command(BaseCommand):
    def handle(self, *args, **options):
        airports.load_openflights_airports_data()
