import abc
from datetime import date
from typing import List

from api.activities.activity_internal_models import (
    AdapterActivity,
    AdapterActivityLocationSearch,
    AdapterActivitySpecificSearch,
    AdapterActivityBookingResponse,
)
from api.activities.activity_models import SimplenightActivityDetailResponse, ActivityVariants
from api.common.base_adapter import BaseAdapter
from api.hotel.models.booking_model import Customer, AdapterActivityBookingRequest


class ActivityAdapter(BaseAdapter, abc.ABC):
    @abc.abstractmethod
    async def search_by_location(self, search: AdapterActivityLocationSearch) -> List[AdapterActivity]:
        pass

    @abc.abstractmethod
    async def search_by_id(self, search: AdapterActivitySpecificSearch) -> AdapterActivity:
        pass

    @abc.abstractmethod
    async def details(self, product_id: str, date_from: date, date_to: date) -> SimplenightActivityDetailResponse:
        pass

    @abc.abstractmethod
    async def variants(self, product_id: str, activity_date: date) -> ActivityVariants:
        pass

    @abc.abstractmethod
    async def book(self, request: AdapterActivityBookingRequest, customer: Customer) -> AdapterActivityBookingResponse:
        pass

    @abc.abstractmethod
    async def cancel(self, order_id: str) -> bool:
        pass
