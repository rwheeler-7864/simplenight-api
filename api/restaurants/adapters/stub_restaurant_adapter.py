import random
import uuid
from datetime import datetime, timedelta
from typing import List

from api.restaurants.restaurant_adapter import RestaurantAdapter
from api.restaurants.restaurant_internal_models import AdapterRestaurant
from api.multi.multi_product_models import RestaurantSearch


class StubRestaurantAdapter(RestaurantAdapter):
    async def search(self, search: RestaurantSearch) -> List[AdapterRestaurant]:
        return list(self._create_restaurant(search) for _ in range(random.randint(2, 25)))

    def _create_restaurant(self, search: RestaurantSearch):
        return AdapterRestaurant(
            restaurant_id=str(uuid.uuid4()),
            name=self._create_restaurant_name(),
            description="Restaurant description",
            reservation_date=search.reservation_date.date(),
            reservation_times=self._create_restaurant_times(search),
        )

    @staticmethod
    def _create_restaurant_name():
        restaurant_name = random.choice(["Original Joe's", "Mathilde's", "Maestro", "Star", "Nick's"])
        food_type = random.choice(["Tapas", "Seafood", "Pasta", "Burgers", "Salad"])

        return f"{restaurant_name} {food_type}"

    @staticmethod
    def _create_restaurant_times(search: RestaurantSearch) -> List[datetime]:
        begin_range = search.reservation_date - timedelta(hours=2)
        return list(begin_range + timedelta(minutes=15 * x) for x in range(16) if random.randint(1, 5) % 5 != 0)

    @classmethod
    def factory(cls, test_mode=True):
        return StubRestaurantAdapter()

    @classmethod
    def get_provider_name(cls):
        return "stub_restaurant"
