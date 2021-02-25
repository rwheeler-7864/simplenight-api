import hashlib
import json
import time
from enum import Enum

import requests

from api import logger
from api.common.common_exceptions import FeatureNotFoundException
from api.common.request_context import get_config
from api.common.transport import Transport
from api.models.models import Feature


class HotelbedsTransport(Transport):
    class Endpoint(Enum):
        HOTELS = "/hotel-api/1.0/hotels"
        BOOKING = "/hotel-api/1.0/bookings"
        CHECKRATES = "/hotel-api/1.0/checkrates"
        HOTEL_CONTENT = "/hotel-content-api/1.0/hotels"
        FACILITIES_TYPES = "/hotel-content-api/1.0/types/facilities"
        CATEGORIES_TYPES = "/hotel-content-api/1.0/types/categories"
        CHAINS_TYPES = "/hotel-content-api/1.0/types/chains"

    def __init__(self, test_mode=True):
        super().__init__()

        self.test_mode = test_mode

    def get(self, endpoint: Endpoint, **params):
        url = self.endpoint(endpoint)

        logger.info(f"Making request to {url}")
        logger.warn(f"Params: {params}")

        response = requests.get(url, params=params, headers=self._get_headers())
        if not response.ok:
            logger.error(f"Error while searching Hotelbeds: {response.text}")

        return response.json()

    def get_by_id(self, endpoint: Endpoint, id: str, **params):
        url = f"{self.endpoint(endpoint)}/{id}"

        logger.info(f"Making request to {url}")
        logger.warn(f"Params: {params}")

        response = requests.get(url, params=params, headers=self._get_headers())
        if not response.ok:
            logger.error(f"Error while searching Hotelbeds: {response.text}")

        return response.json()

    def post(self, endpoint: Endpoint, **params):
        url = self.endpoint(endpoint)

        logger.info(f"Making request to {url}")
        logger.warn(f"Params: {params}")

        response = requests.post(url, data=json.dumps(params), headers=self._get_headers())
        if not response.ok:
            logger.error(f"Error while searching Hotelbeds: {response.text}")

        return response.json()

    def delete(self, endpoint: Endpoint, id: str, **params):
        url = f"{self.endpoint(endpoint)}/{id}"

        logger.info(f"Making request to {url}")
        logger.debug(f"Params: {params}")

        response = requests.delete(url, data=params, headers=self._get_headers())
        if not response.ok:
            logger.error(f"Error while working Hotelbeds: {response.text}")

        return response.json()

    def hotels(self, **params):
        return self.post(self.Endpoint.HOTELS, **params)

    def booking(self, **params):
        return self.post(self.Endpoint.BOOKING, **params)

    def checkrates(self, **params):
        return self.post(self.Endpoint.CHECKRATES, **params)

    def hotel_content(self, **params):
        return self.get(self.Endpoint.HOTEL_CONTENT, **params)

    def facilities_types(self, **params):
        return self.get(self.Endpoint.FACILITIES_TYPES, **params)

    def categories_types(self, **params):
        return self.get(self.Endpoint.CATEGORIES_TYPES, **params)

    def chains_types(self, **params):
        return self.get(self.Endpoint.CHAINS_TYPES, **params)

    def booking_detail(self, id, **params):
        return self.get_by_id(self.Endpoint.BOOKING, id, **params)

    def booking_cancel(self, id, **params):
        return self.delete(self.Endpoint.BOOKING, id, **params)

    def endpoint(self, hotelbeds_endpoint: Endpoint):
        return f"{self._get_host()}{hotelbeds_endpoint.value}"

    def _get_headers(self, **kwargs):
        headers = self._get_default_headers()
        headers["Content-Type"] = "application/json"
        headers["Api-Key"] = self._get_apikey()
        headers["X-Signature"] = self._get_xsignature()
        headers["Accept"] = "application/json"
        headers["Accept-Encoding"] = "gzip"
        headers.update(kwargs)

        return headers

    def _get_credentials(self):
        if self.test_mode:
            return {
                "Api-Key": "ba99fa9f7b504eae563b35b294ef2dcc",
                "Secret": "2e4a7d611f",
            }

        return {
            "Api-Key": get_config(Feature.HOTELBEDS_API_KEY),
            "Secret": get_config(Feature.HOTELBEDS_API_SECRET),
        }

    def _get_apikey(self):
        return self._get_credentials()["Api-Key"]

    def _get_secret(self):
        return self._get_credentials()["Secret"]

    def _get_xsignature(self):
        current_time_in_seconds = int(time.time())
        signature_str = f"{self._get_apikey()}{self._get_secret()}{current_time_in_seconds}"
        return hashlib.sha256(signature_str.encode()).hexdigest()

    def _get_host(self):
        if self.test_mode:
            return "https://api.test.hotelbeds.com"

        try:
            return get_config(Feature.HOTELBEDS_API_URL)
        except FeatureNotFoundException:
            return "https://api.test.hotelbeds.com"
