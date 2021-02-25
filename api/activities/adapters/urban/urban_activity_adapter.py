from typing import Any, Dict

from api.activities.activity_internal_models import (
    AdapterActivitySpecificSearch,
    AdapterActivity,
    AdapterActivityLocationSearch,
)
from api.activities.adapters.suppliers_api.suppliers_api_activity_adapter import SuppliersApiActivityAdapter
from api.activities.adapters.urban.urban_transport import UrbanTransport


class UrbanActivityAdapter(SuppliersApiActivityAdapter):
    @classmethod
    def factory(cls, test_mode=True):
        return UrbanActivityAdapter(UrbanTransport(test_mode=test_mode))

    async def search_by_id(self, search: AdapterActivitySpecificSearch) -> AdapterActivity:
        raise NotImplementedError("Search by ID Not Implemented")

    @classmethod
    def get_provider_name(cls):
        return "urban"

    @staticmethod
    def _get_search_params(search: AdapterActivityLocationSearch) -> Dict[Any, Any]:
        return {
            "date_from": str(search.begin_date),
            "date_to": str(search.end_date),
            "provider_code": search.provider_location_code,
        }
