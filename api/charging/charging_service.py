import requests

from api.charging.constants import CONFIG

class ChargingService:
    def __init__(self, env="development"):
        self.env = env
        self.config = CONFIG[env]
        self.api_key = self.config["api_key"]
        self.token = ""
    
    def generate_header(self):
        if self.token == "":
            return {
                "X-API-Key": self.api_key
            }
        return {
            "X-API-Key": self.api_key,
            "Authorization": "Bearer " + self.token
        }
            

    def get_access_token(self):
        url = self.config["end_point"] + "/profile/authenticate/"
        auth_data = {
            "emailaddress": self.config["email"],
            "password": self.config["password"]
        }

        response = requests.post(url, json=auth_data, headers=self.generate_header())
        return response

    def get_poi(self, request):
        url = self.config["end_point"] + "poi/?"
        for param in request.GET:
            url += param + "=" + request.GET.get(param) + "&" 

        response = requests.get(url, headers=self.generate_header())
        return response

    def get_reference(self, request):
        url = self.config["end_point"] + "referencedata/?"
        for param in request.GET:
            url += param + "=" + request.GET.get(param) + "&" 

        response = requests.get(url, headers=self.generate_header())
        return response

    def get_address(self, request):
        url = self.config["end_point"] + "geocode/?"
        for param in request.GET:
            url += param + "=" + request.GET.get(param) + "&" 

        response = requests.get(url, headers=self.generate_header())
        return response

    def post_comment(self, request):
        url = self.config["end_point"] + "?action=comment_submission&format=json"

        if self.token == "":
            auth_response = self.get_access_token()
            if auth_response.json() and auth_response.json()["Data"]:
                self.token = auth_response.json()["Data"]["access_token"]

        response = requests.post(url, json=request.data, headers=self.generate_header())
        return response
