from api.activities.activity_internal_models import AdapterActivitySpecificSearch, AdapterActivity
from api.activities.adapters.muse.muse_transport import MuseTransport
from api.activities.adapters.suppliers_api.suppliers_api_activity_adapter import SuppliersApiActivityAdapter


class MuseActivityAdapter(SuppliersApiActivityAdapter):
    @classmethod
    def factory(cls, test_mode=True):
        return MuseActivityAdapter(MuseTransport(test_mode=test_mode))

    async def search_by_id(self, search: AdapterActivitySpecificSearch) -> AdapterActivity:
        raise NotImplementedError("Search by ID Not Implemented")

    @classmethod
    def get_provider_name(cls):
        return "musement"
