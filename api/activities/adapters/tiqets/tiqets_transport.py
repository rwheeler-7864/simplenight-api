from datetime import date

from api.activities.adapters.suppliers_api.suppliers_api_transport import SuppliersApiTransport


class TiqetsTransport(SuppliersApiTransport):
    @staticmethod
    def get_supplier_name():
        return "tiqets"

    # Override the details endpoint, since Tiqets uses a separate endpoint
    # Because Tiqets is already in-use in the old booking engine, we can't change the
    # format of the message on the main endpoint.
    def details(self, product_id: str, date_from: date = None, date_to: date = None):
        query_params = {"date_from": str(date_from), "date_to": str(date_to)}
        path_params = [product_id]

        return self.get(self.Endpoint.ACTIVITIES, path_params=path_params, query_params=query_params)
