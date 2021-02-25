from decimal import Decimal
from enum import Enum
from typing import Optional

from api.common.common_models import SimplenightModel


class LocationType(Enum):
    AIRPORT = "AIRPORT"
    CITY = "CITY"


class Location(SimplenightModel):
    # Make LocationResponse hashable
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))

    location_id: str
    language_code: str
    location_name: str
    location_aircode: Optional[str]
    province: Optional[str]
    iso_country_code: str
    latitude: Decimal
    longitude: Decimal
    location_type: LocationType
