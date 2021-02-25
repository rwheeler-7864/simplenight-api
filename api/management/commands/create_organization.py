from django.core.management import BaseCommand

from api.auth.authentication import OrganizationAPIKey
from api.models.models import Organization


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("organization_name", type=str)

    def handle(self, *args, **options):
        organization_name = options.get("organization_name")
        if not organization_name:
            raise RuntimeError("Must pass organization name as a parameter")

        try:
            Organization.objects.get(name=organization_name)
        except Organization.DoesNotExist:
            organization = Organization.objects.create(name=organization_name, api_daily_limit=100, api_burst_limit=5)
            api_key, key = OrganizationAPIKey.objects.create_key(name=organization_name, organization=organization)
            print(key)
            return

        raise RuntimeError("Organization already exists")
