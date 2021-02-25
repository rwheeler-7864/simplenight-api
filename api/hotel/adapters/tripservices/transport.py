from api.common.transport import Transport
from rauth import OAuth2Service
import json


class TripServicesTransport(Transport):
    def __init__(self):
        self.access_token = None

        self.service = OAuth2Service(
            name="tripservices",
            client_id="travelportAPI-3s2TNBrifOdAkjmW5PjRSg74",
            client_secret="3796665fe96cc693bb79755e8c0e0b920ab889d6",
            access_token_url="https://adc-oa-np.apim.travelport.com/oauth/oauth20/token",
            authorize_url="https://adc-oa-np.apiportal-dv.adc-dv-apim.tvlpt/oauth/auz/authorize",
            base_url="https://apigateway.pp.travelport.com/hotel/shop/v8/",
        )

        self.get_access_token()

    def _get_headers(self, **kwargs):
        headers = self._get_default_headers()
        headers["Content-Type"] = "application/json"
        headers["Cache-Control"] = "no-cache"
        headers["Authorization"] = "Bearer " + self.access_token
        headers.update(kwargs)
        return headers

    def get_access_token(self):
        data = {"grant_type": "password", "username": "TP29502017", "password": "Hq0fdEIq", "scope": "openid"}
        session = self.service.get_auth_session(data=data, decoder=json.loads)
        self.access_token = session.access_token

    @classmethod
    def _get_base_url(cls):
        return "https://apigateway.pp.travelport.com/hotel"

    @classmethod
    def _get_properties_url(cls):
        return f"{cls._get_base_url()}/shop/v8/properties"

    @classmethod
    def _get_properties_detail_url(cls):
        return f"{cls._get_base_url()}/shop/v8/propertiesdetail"

    @classmethod
    def _get_availability_url(cls):
        return f"{cls._get_base_url()}/availability/v10/catalogofferingshospitality"

    @classmethod
    def _get_rules_url(cls):
        return f"{cls._get_base_url()}/rules/v8/offershospitality/buildfromrequest"

    @classmethod
    def _get_create_reservation_url(cls):
        return f"{cls._get_base_url()}/book/v7/reservations"

    @classmethod
    def _get_cancel_reservation_url(cls):
        return f"{cls._get_base_url()}/cancel/v7/reservations"

    @classmethod
    def _get_modify_reservation_url(cls):
        return f"{cls._get_base_url()}/book/v7/reservations/"
