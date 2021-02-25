from api.activities.adapters.suppliers_api.suppliers_api_transport import SuppliersApiTransport


class MuseTransport(SuppliersApiTransport):
    @staticmethod
    def get_supplier_name():
        return "musement"
