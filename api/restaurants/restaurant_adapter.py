import abc
from typing import List

from api.common.base_adapter import BaseAdapter
from api.restaurants.restaurant_internal_models import AdapterRestaurant
from api.multi.multi_product_models import RestaurantSearch


class RestaurantAdapter(BaseAdapter, abc.ABC):
    @abc.abstractmethod
    async def search(self, search: RestaurantSearch) -> List[AdapterRestaurant]:
        pass
