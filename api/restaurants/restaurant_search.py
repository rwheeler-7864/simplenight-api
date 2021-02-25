import asyncio
from typing import List

from api.hotel.adapters import adapter_service
from api.restaurants.restaurant_internal_models import AdapterRestaurant
from api.restaurants.restaurant_models import SimplenightRestaurant
from api.multi.multi_product_models import RestaurantSearch


def search(restaurant_search: RestaurantSearch) -> List[SimplenightRestaurant]:
    restaurants = list(_search_all_adapters(restaurant_search))
    return _process_restaurants(restaurants)


def _process_restaurants(restaurants: List[AdapterRestaurant]) -> List[SimplenightRestaurant]:
    """Process restaurant reservations returned from an adapter, and return SimplenightRestaurant.
    For now this is just scaffolding.
    """

    return list(map(_adapter_to_simplenight_restaurant, restaurants))


def _adapter_to_simplenight_restaurant(adapter_restaurant: AdapterRestaurant) -> SimplenightRestaurant:
    return SimplenightRestaurant(
        restaurant_id=adapter_restaurant.restaurant_id,
        name=adapter_restaurant.name,
        description=adapter_restaurant.description,
        reservation_date=adapter_restaurant.reservation_date,
        reservation_times=adapter_restaurant.reservation_times,
    )


def _search_all_adapters(restaurant_search: RestaurantSearch) -> List[AdapterRestaurant]:
    adapters = adapter_service.get_restaurant_adapters_to_search(restaurant_search)
    for adapter in adapters:
        yield from asyncio.run(adapter.search(restaurant_search))
