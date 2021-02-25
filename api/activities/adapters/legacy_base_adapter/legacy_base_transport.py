import abc
import urllib.parse
from enum import Enum
from typing import Dict, List

from api.activities.adapters.suppliers_api.suppliers_api_transport import SuppliersApiTransport


class LegacyBaseTransport(SuppliersApiTransport, abc.ABC):
    class Endpoint(Enum):
        SEARCH = "search"
        DETAILS = "details"

    def get_endpoint(self, endpoint: Endpoint, path_params: List = None, query_params: Dict = None):
        base_url = f"{self.get_host()}/{self.get_supplier_name()}/{endpoint.value}"
        if path_params:
            path_url = str.join("/", path_params)
            base_url = f"{base_url}/{path_url}"

        if not query_params:
            return base_url

        return f"{base_url}?{urllib.parse.urlencode(query_params)}"

    def get_host(self):
        if self.test_mode:
            return "http://suppliers-qa.simplenight.com"
        else:
            return "https://suppliers.simplenight.com"
