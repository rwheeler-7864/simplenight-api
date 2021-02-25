from django.core.management import BaseCommand

from api.hotel.parsers.giata import GiataParser


class Command(BaseCommand):
    def handle(self, *args, **options):
        giata = GiataParser()
        giata.execute_hotel_guide()
