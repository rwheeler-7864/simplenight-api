import abc
from datetime import date
from typing import List, Dict, Any

from api import logger
from api.activities.activity_adapter import ActivityAdapter
from api.activities.activity_internal_models import (
    AdapterActivityBookingResponse,
    AdapterActivitySpecificSearch,
    AdapterActivity,
    AdapterActivityLocationSearch,
)
from api.activities.activity_models import ActivityVariants, SimplenightActivityDetailResponse
from api.activities.adapters.legacy_base_adapter.legacy_base_transport import LegacyBaseTransport
from api.hotel.models.booking_model import AdapterActivityBookingRequest, Customer
from api.hotel.models.hotel_api_model import Image
from api.hotel.models.hotel_common_models import Money


class LegacyActivityAdapter(ActivityAdapter, abc.ABC):
    def __init__(self, transport: LegacyBaseTransport):
        self.transport = transport

    async def search_by_location(self, search: AdapterActivityLocationSearch) -> List[AdapterActivity]:
        request_params = self._get_search_params(search)
        logger.info(f"Searching {self.get_provider_name()} with params: {request_params}")
        response = self.transport.search(**request_params)

        return list(map(lambda x: self._create_activity(x, activity_date=search.begin_date), response["result"]))

    async def search_by_id(self, search: AdapterActivitySpecificSearch) -> AdapterActivity:
        pass

    async def details(self, product_id: str, date_from: date, date_to: date) -> SimplenightActivityDetailResponse:
        pass

    async def variants(self, product_id: str, activity_date: date) -> ActivityVariants:
        pass

    async def book(self, request: AdapterActivityBookingRequest, customer: Customer) -> AdapterActivityBookingResponse:
        pass

    async def cancel(self, order_id: str) -> bool:
        pass

    def _create_activity(self, activity, activity_date: date):
        total_price = activity["total_price"]

        return AdapterActivity(
            name=activity["name"],
            provider=self.get_provider_name(),
            code=activity["code"],
            description=activity["description"],
            activity_date=activity_date,
            total_price=Money(amount=total_price["amount"], currency=total_price["currency"]),
            categories=activity["categories"],
            images=list(Image(url=image, display_order=idx) for idx, image in enumerate(activity["images"])),
        )

    @staticmethod
    def _get_search_params(search: AdapterActivityLocationSearch) -> Dict[Any, Any]:
        return {
            "date_from": str(search.begin_date),
            "date_to": str(search.end_date),
            "location": {"longitude": str(search.location.longitude), "latitude": str(search.location.latitude)},
        }
