from api.activities.adapters.suppliers_api.suppliers_api_transport import SuppliersApiTransport


class TravelcuriousTransport(SuppliersApiTransport):
    @staticmethod
    def get_supplier_name():
        return "travelcurious"
