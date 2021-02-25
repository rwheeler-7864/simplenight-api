from django.core.management import BaseCommand

from api.locations.city_mapping import CityMappingService


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("provider_name", type=str)

    def handle(self, *args, **options):
        provider_name = options.get("provider_name")
        if not provider_name:
            raise RuntimeError("Must pass provider name")

        mapping_service = CityMappingService(provider_name=options["provider_name"])
        mapping_service.map_cities()
