import abc
import json
from typing import Dict, Any

import requests

from api import logger
from api.common.common_models import SimplenightModel


class Transport(abc.ABC):
    def __init__(self):
        self._headers = {
            "Accept-Encoding": "gzip",
        }

    @abc.abstractmethod
    def _get_headers(self, **kwargs):
        pass

    def _get_default_headers(self):
        return self._headers.copy()

    def post(self, url, params: Dict, **kwargs):
        params.update(kwargs)

        response = requests.post(f"{self._get_host()}{url}", data=params, headers=self._get_headers())
        self._log_request(f"POST {self._get_host()}{url}", params, response)

        return response.json()

    def post_form(self, url, params: Dict, **kwargs):
        params.update(kwargs)

        response = requests.post(f"{self._get_host()}{url}", data=params, headers=self._get_headers(**{"Content-Type": "application/x-www-form-urlencoded"}))
        self._log_request(f"POST PARAMS {self._get_host()}{url}", params, response)

        return response.json()

    def get(self, url, params: Dict, **kwargs):
        params.update(kwargs)

        response = requests.get(f"{self._get_host()}{url}", params=params, headers=self._get_headers())
        self._log_request(f"GET {self._get_host()}{url}", params, response)

        return response.json()

    def _get_host(self):
        return ""

    @staticmethod
    def _log_request(url, request, response):
        if hasattr(request, "json"):
            request = request.json()

        logger.debug(
            {
                "url": url,
                "request": request,
                "status": response.ok,
                "status_code": response.status_code,
                "response": response.text,
            }
        )
