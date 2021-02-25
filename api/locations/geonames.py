import csv
from contextlib import closing
from io import BytesIO
from typing import List, Sequence
from urllib.request import urlopen
from zipfile import ZipFile

from django.conf import settings

from api import logger
from api.models.models import Geoname, GeonameAlternateName
from common import utils


class GeonameSettings:
    @property
    def supported_languages(self):
        return settings.GEONAMES_SUPPORTED_LANGUAGES

    @property
    def supported_location_types(self):
        return settings.GEONAMES_SUPPORTED_LOCATION_TYPES

    @property
    def geonames_cities_url(self):
        return settings.GEONAMES_CITIES_URL

    @property
    def geonames_cities_filename(self):
        return settings.GEONAMES_CITIES_FILENAME

    @classmethod
    def get_alternate_names_url(cls, country_code):
        base_url = settings.GEONAMES_ALT_NAMES_BASE_URL
        return f"{base_url}/{country_code}.zip"

    @classmethod
    def get_alternate_names_filename(cls, country_code):
        return f"{country_code}.txt"


class GeonamesParser:
    def __init__(self, config: GeonameSettings):
        self.config = config

    def download_and_parse(self):

        logger.info("Removing old Geoname entries")
        Geoname.objects.all().delete()

        cities = set()
        countries = set()
        logger.info("Parsing main cities DB")

        for chunk in utils.chunks(self._download_parse_main_db(), 1000):
            models = list(filter(self._filter_main_db, map(self._create_geoname_model, chunk)))
            Geoname.objects.bulk_create(models)

            for model in models:
                cities.add(model.geoname_id)
                countries.add(model.iso_country_code)

        for country in sorted(countries):
            logger.info("Loading Geoname alternate names for " + country)

            alternate_names_rows = self._download_and_parse_languages(country)
            alternate_names = map(self._create_alternate_name_model, alternate_names_rows)

            models_to_save = []
            for alternate_name_model in filter(self._filter_alternate_names, alternate_names):
                if alternate_name_model.geoname_id in cities:
                    models_to_save.append(alternate_name_model)

                if len(models_to_save) > 1000:
                    GeonameAlternateName.objects.bulk_create(models_to_save)
                    models_to_save.clear()

            GeonameAlternateName.objects.bulk_create(models_to_save)

    def _download_parse_main_db(self):
        return self._download_and_parse(self.config.geonames_cities_url, self.config.geonames_cities_filename)

    def _download_and_parse_languages(self, country_code):
        url = self.config.get_alternate_names_url(country_code)
        filename = self.config.get_alternate_names_filename(country_code)

        return self._download_and_parse(url, filename)

    def _filter_main_db(self, geoname: Geoname):
        return geoname.location_type in self.config.supported_location_types

    def _filter_alternate_names(self, alternate_name: GeonameAlternateName):
        if alternate_name.iso_language_code not in self.config.supported_languages:
            return False

        if alternate_name.is_colloquial:
            return False

        if alternate_name.is_short_name:
            return False

        return True

    @staticmethod
    def _create_alternate_name_model(row) -> GeonameAlternateName:
        return GeonameAlternateName(
            alternate_name_id=row[0],
            geoname_id=row[1],
            iso_language_code=row[2],
            name=row[3],
            is_preferred=row[4] == "1",
            is_short_name=row[5] == "1",
            is_colloquial=row[6] == "1",
        )

    @staticmethod
    def _create_geoname_model(row) -> Geoname:
        return Geoname(
            geoname_id=row[0],
            location_name=row[2],
            latitude=row[4],
            longitude=row[5],
            iso_country_code=row[8],
            province=row[10],
            population=row[14],
            timezone=row[17],
            location_type=row[7]
        )

    @staticmethod
    def _download_and_parse(url, filename) -> List[Sequence[str]]:
        with closing(urlopen(url)) as response:
            zipfile = ZipFile(BytesIO(response.read()))
            cities_archive = zipfile.open(filename)

            lines = map(lambda x: x.decode("utf-8"), cities_archive.readlines())
            yield from csv.reader(lines, delimiter="\t")
