from api.activities.adapters.legacy_base_adapter.legacy_base_adapter import LegacyActivityAdapter
from api.activities.adapters.tourcms.tourcms_transport import TourCmsTransport


class TourCmsActivityAdapter(LegacyActivityAdapter):
    @classmethod
    def factory(cls, test_mode=True):
        return TourCmsActivityAdapter(TourCmsTransport(test_mode=test_mode))

    @classmethod
    def get_provider_name(cls):
        return "tourcms"
