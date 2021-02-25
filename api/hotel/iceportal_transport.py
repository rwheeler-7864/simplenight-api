import warnings

from requests.auth import HTTPBasicAuth
from requests.sessions import Session
from zeep import Client, Transport


class IcePortalTransport:
    def __init__(self):
        self.session = self._create_wsdl_session()
        self.client = self._get_wsdl_client()

    def create_service(self, binding_name):
        target_namespace = "http://services.iceportal.com/service"
        service_binding = f"{{{target_namespace}}}{binding_name}"
        return self.client.create_service(service_binding, self._get_url())

    def get_service(self):
        return self.create_service("ICEWebServiceSoap")

    def get_auth_header(self):
        return {"ICEAuthHeaderWithMType": {"Username": self._get_username(), "Password": self._get_password()}}

    def _create_wsdl_session(self):
        session = Session()
        session.auth = HTTPBasicAuth(self._get_username(), self._get_password())
        return session

    def _get_wsdl_client(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning, 338)
            wsdl_path = self._get_wsdl_path()
            return Client(wsdl_path, transport=Transport(session=self.session))

    @staticmethod
    def _get_wsdl_path():
        return "http://services.iceportal.com/Service.asmx?WSDL"

    @staticmethod
    def _get_username():
        return "distributor@simplenight.com"

    @staticmethod
    def _get_password():
        return "Gp*3eA"

    @staticmethod
    def _get_url():
        return "http://services.iceportal.com/Service.asmx"