import csv
from typing import Any, Dict

from api.hotel.adapters.priceline.priceline_info import PricelineInfo
from api.models.models import ProviderCity
from common import utils


class PricelineCityParser:
    CITY_FILE_PATH = "resources/priceline/cities.csv"

    def __init__(self):
        self.provider = PricelineInfo().get_or_create_provider_id()

    def parse(self):
        with open(self.CITY_FILE_PATH, "r") as f:
            reader = csv.DictReader(f)
            models = list(self._parse_row_to_model(row) for row in reader)

        ProviderCity.objects.all().delete()

        for chunk in utils.chunks(models, 100):
            ProviderCity.objects.bulk_create(chunk)

    def _parse_row_to_model(self, row: Dict[str, Any]):
        return ProviderCity(
            provider=self.provider,
            provider_code=row["cityid_ppn"],
            location_name=row["city"],
            province=row["state_code"],
            country_code=row["country_code"],
            latitude=row["latitude"],
            longitude=row["longitude"],
        )