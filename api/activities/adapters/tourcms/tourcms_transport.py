from api.activities.adapters.legacy_base_adapter.legacy_base_transport import LegacyBaseTransport


class TourCmsTransport(LegacyBaseTransport):
    @staticmethod
    def get_supplier_name():
        return "grayline-lasvegas"
