#!/usr/bin/env python

from django.core.management.base import BaseCommand

from api import logger
from api.hotel.iceportal_transport import IcePortalTransport
from api.hotel.models.hotel_api_model import ImageType
from api.models.models import ProviderImages, Provider


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.transport = IcePortalTransport()
        self.provider = Provider.objects.get_or_create(name="iceportal")[0]

    def handle(self, *args, **options):
        existing_images = ProviderImages.objects.filter(provider__name="iceportal")

        logger.info(f"Removing existing iceportal images: {existing_images.count()}")
        existing_images.delete()

        properties = self.transport.get_service().GetProperties(_soapheaders=self.transport.get_auth_header())

        for iceportal_property in properties["info"]["PropertyIDInfo"]:
            mapped_id = iceportal_property["mappedID"]
            logger.info("Parsing images for IcePortal ID: " + mapped_id)
            try:
                self._parse_and_save_images(mapped_id)
            except Exception:
                logger.exception("Error while loading hotel")

    def _parse_and_save_images(self, iceportal_id):
        visuals = self.transport.get_service().GetVisualsV2(
            _soapheaders=self.transport.get_auth_header(), MappedID=iceportal_id
        )

        iceportal_id = visuals["Property"]["PropertyInfo"]["iceID"]
        images = visuals["Property"]["MediaGallery"]["Pictures"]["ImagesV2"]["PropertyImageVisualsV2"]

        provider_image_models = []
        for image in images:
            display_order = image["ordinal"]
            fullsize_url = image["DirectLinks"]["Url"]
            provider_image_models.append(
                ProviderImages(
                    provider=self.provider,
                    provider_code=iceportal_id,
                    display_order=display_order,
                    type=ImageType.UNKNOWN.value,
                    image_url=str.replace(fullsize_url, "http://", "//"),
                )
            )

        ProviderImages.objects.bulk_create(provider_image_models)
