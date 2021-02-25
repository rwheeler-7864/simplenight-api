from enum import Enum

import requests

from api import logger
from api.common.common_exceptions import FeatureNotFoundException
from api.common.request_context import get_config
from api.common.transport import Transport
from api.models.models import Feature


class PricelineTransport(Transport):
    class Endpoint(Enum):
        HOTEL_EXPRESS = "/hotel/getExpress.Results"
        HOTEL_DETAILS = "/hotel/getHotelDetails"
        EXPRESS_BOOK = "/hotel/getExpress.Book"
        EXPRESS_LOOKUP = "/hotel/getExpress.LookUp"
        EXPRESS_CANCEL = "/hotel/getExpress.Cancel"
        EXPRESS_CONTRACT = "/hotel/getExpress.Contract"
        HOTELS_DOWNLOAD = "/shared/getBOF2.Downloads.Hotel.Hotels"
        PHOTOS_DOWNLOAD = "/shared/getBOF2.Downloads.Hotel.Photos"
        SALES_REPORT = "/shared/getTRK.Sales.Select.Hotel"
        AMENITIES = "/shared/getBOF2.Downloads.Hotel.Amenities"
        HOTEL_CHAINS = "/shared/getBOF2.Downloads.Hotel.Chains"
        POLICIES = "/shared/getPolicy.Hotel"
        REVIEWS = "/hotel/getReviews"

    def __init__(self, test_mode=True, refid="10046"):
        super().__init__()
        self.test_mode = test_mode
        self.priceline_refid = refid

        self.TEST_MODE_CREDENTIALS = {
            "refid": self.priceline_refid,
            "api_key": "990b98b0a0efaa7acf461ff6a60cf726",
        }

        self.PRODUCTION_CREDENTIALS = {
            "refid": self.priceline_refid,
            "api_key": "0902461455a8fd238cb0b3d4b8276f91",
        }

    def get(self, endpoint: Endpoint, **params):
        url = self.endpoint(endpoint)
        params.update(self._get_default_params())

        logger.info(f"Making request to {url}")
        logger.debug(f"Params: {params}")

        response = requests.get(url, params=params, headers=self._get_headers())
        logger.info(f"Request complete to {url}")

        if not response.ok:
            logger.error(f"Error while searching Priceline: {response.text}")

        return response.json()

    def post(self, endpoint: Endpoint, **params):
        url = self.endpoint(endpoint)
        params.update(self._get_default_params())

        logger.info(f"Making request to {url}")
        logger.debug(f"Params: {params}")

        response = requests.post(url, data=params, headers=self._get_headers())
        logger.info(f"Request complete to {url}")

        if not response.ok:
            logger.error(f"Error while searching Priceline: {response.text}")

        return response.json()

    def hotel_express(self, **params):
        return self.get(self.Endpoint.HOTEL_EXPRESS, **params)

    def hotel_details(self, **params):
        return self.get(self.Endpoint.HOTEL_DETAILS, **params)

    def hotel_reviews(self, **params):
        return self.get(self.Endpoint.REVIEWS, **params)

    def express_book(self, **params):
        return self.post(self.Endpoint.EXPRESS_BOOK, **params)

    def express_contract(self, **params):
        return self.post(self.Endpoint.EXPRESS_CONTRACT, **params)

    def express_lookup(self, **params):
        return self.post(self.Endpoint.EXPRESS_LOOKUP, **params)

    def express_cancel(self, **params):
        return self.post(self.Endpoint.EXPRESS_CANCEL, **params)

    def hotels_download(self, **params):
        return self.get(self.Endpoint.HOTELS_DOWNLOAD, **params)

    def photos_download(self, **params):
        return self.get(self.Endpoint.PHOTOS_DOWNLOAD, **params)

    def policies_download(self, **params):
        return self.get(self.Endpoint.POLICIES, **params)

    def endpoint(self, priceline_endpoint: Endpoint):
        return f"{self._get_host()}{priceline_endpoint.value}"

    def _get_headers(self, **kwargs):
        headers = self._get_default_headers()
        headers.update(kwargs)

        return headers

    def _get_default_params(self):
        return {**self._get_credentials(), "format": "json2"}

    def _get_credentials(self):
        if self.test_mode:
            return self.TEST_MODE_CREDENTIALS

        return self.PRODUCTION_CREDENTIALS

    def _get_host(self):
        if not self.test_mode:
            return "https://api.rezserver.com/api"

        try:
            return get_config(Feature.PRICELINE_API_URL)
        except FeatureNotFoundException:
            return "https://api-sandbox.rezserver.com/api"

    def sales_report(self, **params):
        return self.get(self.Endpoint.SALES_REPORT, **params)
