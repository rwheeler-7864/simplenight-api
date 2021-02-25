import decimal

from django.test import TestCase

from api.locations import geonames
from api.locations.geonames import GeonameSettings
from api.models.models import Geoname, GeonameAlternateName
from api.tests.utils import get_test_resource_path


class TestGeonamesCommand(TestCase):
    def test_download_and_parse(self):
        class GeonameTestSettings(GeonameSettings):
            @property
            def geonames_cities_url(self):
                return f"file://{get_test_resource_path('cities-sample.zip')}"

            @classmethod
            def get_alternate_names_url(cls, country_code):
                return f"file://{get_test_resource_path('US-alternate-names-sample.zip')}"

        self.assertEqual(0, Geoname.objects.count())

        geonames_cmd = geonames.GeonamesParser(GeonameTestSettings())
        geonames_cmd.download_and_parse()

        self.assertEqual(4, Geoname.objects.count())
        self.assertEqual(29, GeonameAlternateName.objects.count())

        location = Geoname.objects.get(geoname_id="5391959")
        self.assertEqual("San Francisco", location.location_name)
        self.assertEqual("CA", location.province)
        self.assertEqual("US", location.iso_country_code)
        self.assertEqual("San Francisco", location.location_name)
        self.assertEqual(decimal.Decimal("37.774930"), location.latitude)
        self.assertEqual(decimal.Decimal("-122.419420"), location.longitude)
        self.assertEqual(864816, location.population)
        self.assertEqual("America/Los_Angeles", location.timezone)

        Geoname.objects.prefetch_related("lang").filter(geoname_id=5391959).first()

        localization = GeonameAlternateName.objects.filter(
            geoname__iso_country_code="US", iso_language_code="ja", geoname_id="5391959"
        )
        self.assertEqual("サンフランシスコ", localization.first().name)
