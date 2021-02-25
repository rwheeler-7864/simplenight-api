import uuid
from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase
from rest_framework.test import APIClient

from api.auth.authentication import OrganizationAPIKey
from api.common import request_context
from api.hotel import markups
from api.models.models import Organization, Feature
from api.common.context_middleware import RequestContextMiddleware
from api.common.request_cache import RequestCacheMiddleware


class SimplenightTestCase(TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.organization_name = str(uuid.uuid4())

    def setUp(self) -> None:
        markups.DEFAULT_MARKUP = Decimal("0.12")
        self.request_cache = RequestCacheMiddleware(Mock())
        self.request_context = RequestContextMiddleware()
        self.organization = self.create_organization(self.organization_name)

        self.api_key = self.create_api_key(self.organization)
        self.client = APIClient(HTTP_X_API_KEY=self.api_key)
        self.mock_request()
        self.stub_feature(Feature.TEST_MODE, "true")

    def create_organization_and_client(self, organization_name, api_burst_limit=5, api_daily_limit=100):
        organization = self.create_organization(organization_name, api_burst_limit, api_daily_limit)
        api_key = self.create_api_key(organization)
        return APIClient(HTTP_X_API_KEY=api_key)

    def mock_request(self):
        # Since we're not executing a real request, set the organization on the context
        mock_request = Mock()
        mock_request.META = {"HTTP_X_API_KEY": self.api_key}
        self.request_cache.process_request(mock_request)
        self.request_context.process_request(mock_request)

    @staticmethod
    def create_organization(organization_name, api_burst_limit=5, api_daily_limit=100):
        try:
            existing_organization = Organization.objects.get(name=organization_name)
            existing_organization.delete()
        except Organization.DoesNotExist:
            pass

        return Organization.objects.create(
            name=organization_name, api_daily_limit=api_daily_limit, api_burst_limit=api_burst_limit
        )

    @staticmethod
    def create_api_key(organization):
        _, key = OrganizationAPIKey.objects.create_key(name="test-key", organization=organization)
        return key

    def stub_feature(self, feature: Feature, value):
        request_context.clear_cache()
        self.organization.set_feature(feature, value)

    def clear_feature(self, feature: Feature):
        self.organization.clear_feature(feature)
        request_context.clear_cache()

    def post(self, endpoint, obj, content_type="application/json"):
        data = obj.json()
        return self.client.post(endpoint, data=data, content_type=content_type)

    def get(self, endpoint, **kwargs):
        return self.client.get(endpoint, data=kwargs)
