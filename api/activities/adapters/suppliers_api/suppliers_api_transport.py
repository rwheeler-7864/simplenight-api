import abc
import urllib.parse
from datetime import date
from enum import Enum
from typing import Dict, List

import requests

from api import logger
from api.common.transport import Transport


class SuppliersApiTransport(Transport, abc.ABC):
    def __init__(self, test_mode=True):
        super().__init__()
        self.test_mode = test_mode

    class Endpoint(Enum):
        SEARCH = "search"
        DETAILS = "details"
        VARIANTS = "variants"
        BOOK = "book"
        CANCEL = "cancel"
        ACTIVITIES = "activities"

    def _get_headers(self, **kwargs):
        return {
            "Content-Type": "application/json",
        }

    def search(self, **data):
        return self.post(self.Endpoint.SEARCH, **data)

    def details(self, product_id: str, date_from: date = None, date_to: date = None):
        query_params = {"date_from": str(date_from), "date_to": str(date_to)}
        path_params = [product_id]

        return self.get(self.Endpoint.ACTIVITIES, path_params=path_params, query_params=query_params)

    def variants(self, product_id, activity_date):
        path_params = [product_id, "date", str(activity_date)]
        return self.get(self.Endpoint.VARIANTS, path_params=path_params)

    def book(self, **data):
        return self.post(self.Endpoint.BOOK, **data)

    def cancel(self, **data):
        return self.post(self.Endpoint.CANCEL, **data)

    def get(self, endpoint: Endpoint, path_params: List = None, query_params: Dict = None):
        url = self.get_endpoint(endpoint, path_params=path_params, query_params=query_params)
        logger.info(f"Making GET request to {url}")

        response = requests.get(url, headers=self._get_headers())
        logger.info(f"GET Request complete to {url}")

        if not response.ok:
            logger.error(f"Error while searching Suppliers API: {response.text}")

        return response.json()

    def post(self, endpoint: Endpoint, path_params: List = None, query_params: Dict = None, **params):
        url = self.get_endpoint(endpoint, path_params=path_params, query_params=query_params)

        logger.info(f"Making POST request to {url}")
        logger.debug(f"Params: {params}")

        response = requests.post(url, json=params, headers=self._get_headers())
        logger.info(f"POST Request complete to {url}")

        if not response.ok:
            logger.error(f"Error while searching Suppliers API: {response.text}")

        return response.json()

    @staticmethod
    @abc.abstractmethod
    def get_supplier_name():
        pass

    @classmethod
    def get_endpoint(cls, endpoint: Endpoint, path_params: List = None, query_params: Dict = None):
        base_url = f"https://suppliers-api.qa-new.simplenight.com/v1/{cls.get_supplier_name()}/{endpoint.value}"
        if path_params:
            path_url = str.join("/", path_params)
            base_url = f"{base_url}/{path_url}"

        if not query_params:
            return base_url

        return f"{base_url}?{urllib.parse.urlencode(query_params)}"
