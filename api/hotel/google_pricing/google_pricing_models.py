from datetime import date
from typing import List

from api.common.common_models import SimplenightModel


class GooglePricingItineraryQuery(SimplenightModel):
    checkin: date
    nights: int
    hotel_codes: List[str]

