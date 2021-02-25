from django.test import TestCase

from api.hotel.parsers.giata import GiataParser


class TestGiataOnline(TestCase):
    def setUp(self) -> None:
        self.giata = GiataParser()

    def test_parse_properties(self):
        self.giata.execute()

    def test_parse_hotel_guides(self):
        self.giata.execute_hotel_guide()
