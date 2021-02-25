import abc

from django.core.management import BaseCommand
from django.db.models import Q

from api.common.context_middleware import RequestContextMiddleware
from api.common.request_cache import RequestCacheMiddleware
from api.models.models import Organization


class SimplenightBaseCommand(BaseCommand, abc.ABC):
    def __init__(self):
        self.mock_organization()
        super().__init__()

    @staticmethod
    def mock_organization():
        RequestCacheMiddleware(None).process_request(None)
        RequestContextMiddleware.mock_organization(Organization.objects.filter(Q(name="simplenight"))[0])
