import requests

from api.carey.settings import CONFIG


class CareySearch:
    def __init__(self):
        self.config = CONFIG
        self.app_id = self.config["app_id"]
        self.app_key = self.config["app_key"]

    def generate_header(self):
        return {"app_id": self.app_id, "app_key": self.app_key}

    def search_reservation(self, request):
        url = "https://api.carey.com:8443/sandbox/CSIProfile_v2/rest/jsonSearchTrips/searchTrips"
        response = requests.post(url, json=request.data, headers=self.generate_header())
        return response
