from django.test import Client

from api.models.models import Organization, Feature
from api.tests.unit.simplenight_test_case import SimplenightTestCase

ENDPOINT = "/api/v1/hotels/status"


class TestOrganizationsAndAuthentication(SimplenightTestCase):
    def __init__(self, *args):
        super().__init__(*args)

    def test_authentication_required(self):
        client_without_credentials = Client()
        response = client_without_credentials.get(ENDPOINT)
        self.assertEqual(401, response.status_code)
        self.assertEqual("Authentication credentials were not provided.", response.json()["detail"])

        response = self.client.get(ENDPOINT)

        self.assertEqual(200, response.status_code)

    def test_api_quota_for_anonymous_organization(self):
        client = self.create_organization_and_client("QuotaTest", api_burst_limit=5, api_daily_limit=100)

        self.assertEqual(200, client.get(ENDPOINT).status_code)
        self.assertEqual(200, client.get(ENDPOINT).status_code)
        self.assertEqual(200, client.get(ENDPOINT).status_code)
        self.assertEqual(200, client.get(ENDPOINT).status_code)
        self.assertEqual(200, client.get(ENDPOINT).status_code)

        # Throttled after 5 requests
        self.assertEqual(429, client.get(ENDPOINT).status_code)

    def test_organization_features(self):
        organization = Organization.objects.create(name="foo", api_daily_limit=100, api_burst_limit=5)
        self.assertIsNone(organization.get_feature(Feature.ENABLED_ADAPTERS))

        organization.set_feature(Feature.ENABLED_ADAPTERS, "priceline")
        self.assertEqual("priceline", organization.get_feature(Feature.ENABLED_ADAPTERS))

    def test_status_page_request_cache(self):
        client = self.create_organization_and_client("TestOrganization")
        response = client.get(ENDPOINT)
        self.assertEqual(200, response.status_code)
        self.assertEqual("OK TestOrganization", response.data)
