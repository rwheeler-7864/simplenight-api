from datetime import datetime, date
from typing import List, Optional

from api.common.common_models import SimplenightModel
from api.hotel.models.hotel_api_model import Image


class AdapterRestaurant(SimplenightModel):
    restaurant_id: str
    name: str
    description: str
    reservation_date: date
    reservation_times: List[datetime]
    images: Optional[List[Image]]
