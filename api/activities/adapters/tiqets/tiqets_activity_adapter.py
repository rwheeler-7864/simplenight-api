from api.activities.activity_internal_models import AdapterActivitySpecificSearch, AdapterActivity
from api.activities.adapters.suppliers_api.suppliers_api_activity_adapter import SuppliersApiActivityAdapter
from api.activities.adapters.tiqets.tiqets_transport import TiqetsTransport


class TiqetsActivityAdapter(SuppliersApiActivityAdapter):
    @classmethod
    def factory(cls, test_mode=True):
        return TiqetsActivityAdapter(TiqetsTransport(test_mode=test_mode))

    async def search_by_id(self, search: AdapterActivitySpecificSearch) -> AdapterActivity:
        raise NotImplementedError("Search by ID Not Implemented")

    @classmethod
    def get_provider_name(cls):
        return "tiqets"
