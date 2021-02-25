from enum import Enum
import hashlib
import time
import requests
import json

from api import logger
from api.common.common_exceptions import FeatureNotFoundException
from api.common.request_context import get_config
from api.dining.adapters.transport import Transport
from api.models.models import Feature

"""
Yelp Reservation API Wrapper.
Documentation: https://docs.developer.yelp.com/docs/endpoints-4
"""

class YelpTransport(Transport):
    def __init__(self, test_mode=True):
        super().__init__()

        self.test_mode = test_mode

    def businesses(self, **params):
        return self.get("/businesses/search", **params)

    def business_details(self, id, **params):
        return self.get(f"/businesses/{id}", **params)

    def business_reviews(self, id, **params):
        return self.get(f"/businesses/{id}/reviews", **params)

    def business_openings(self, id, **params):
        return self.get(f"/bookings/{id}/openings", **params)

    def booking_hold(self, id, **params):
        return self.post_form(f"/bookings/{id}/holds", **params)

    def booking(self, id, **params):
        return self.post_form(f"/bookings/{id}/reservations", **params)

    def booking_cancel(self, id, **params):
        return self.post(f"/bookings/reservation/{id}/cancel", **params)

    def _get_headers(self, **kwargs):
        headers = self._get_default_headers()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = self._get_authorization()
        headers["Accept"] = "application/json"
        headers["Accept-Encoding"] = "gzip"
        headers.update(kwargs)

        return headers

    def _get_credentials(self):
        if self.test_mode:
            return {
                "Client-ID": "Kvkm8OeQoWBdxRs7LJfQbg",
                "Api-Key": "EC-cpclHrDk7wA8R5_rbbbaYAd6D8DTPaL1EBHaUGYT2ziUnDlTndRnG2J2yggm44pe6_dUs942BdtWju_Fs7t15ZY1JeWM-snDG-Ui146rylLWPAf4aQE7vBiP-X3Yx"
            }

        return {
            "Client-ID": "Kvkm8OeQoWBdxRs7LJfQbg",
            "Api-Key": "EC-cpclHrDk7wA8R5_rbbbaYAd6D8DTPaL1EBHaUGYT2ziUnDlTndRnG2J2yggm44pe6_dUs942BdtWju_Fs7t15ZY1JeWM-snDG-Ui146rylLWPAf4aQE7vBiP-X3Yx"
        }

    def _get_client_id(self):
        return self._get_credentials()["Client-ID"]

    def _get_authorization(self):
        return f"Bearer {self._get_credentials()['Api-Key']}"

    def _get_host(self):
        return "https://api.yelp.com/v3"
