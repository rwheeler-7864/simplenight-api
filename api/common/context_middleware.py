import uuid

from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_api_key.permissions import KeyParser

from api import logger
from api.auth.authentication import OrganizationAPIKey
from api.common.request_cache import get_request_cache
from api.models.models import Organization


class RequestContextMiddleware(MiddlewareMixin):
    @classmethod
    def process_request(cls, request: HttpRequest):
        request_cache = get_request_cache()
        organization = cls.get_organization_from_api_key_in_request(request)

        request_cache.set("organization", organization)
        request_cache.set("request_id", str(uuid.uuid4()))

    @classmethod
    def mock_organization(cls, organization: Organization):
        # Hack for a request context in a Django Command
        request_cache = get_request_cache()
        request_cache.set("organization", organization)
        request_cache.set("request_id", str(uuid.uuid4()))

    @classmethod
    def get_organization_from_api_key_in_request(cls, request: HttpRequest):
        key_parser = KeyParser()
        api_key = key_parser.get(request)
        if api_key:
            try:
                organization_api_key = OrganizationAPIKey.objects.get_from_key(api_key)
                logger.info(f"Matched organization {organization_api_key.organization.name} from API key")
                return organization_api_key.organization
            except OrganizationAPIKey.DoesNotExist:
                logger.error("Invalid API Key, could not set organization")

        try:
            http_user = BasicAuthentication().authenticate(request)
            if http_user:
                try:
                    http_user = http_user[0]
                    organization = Organization.objects.get(username=http_user)
                    logger.info(f"Matched organization {organization.name} from user {http_user}")
                    return organization
                except Organization.DoesNotExist:
                    logger.error(f"Could not find organization or user {http_user}")
        except AuthenticationFailed:
            logger.error(f"Could not authenticate user")
