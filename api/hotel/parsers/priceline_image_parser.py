from unittest.mock import Mock

from api import logger
from api.common.request_cache import RequestCacheMiddleware
from api.hotel.adapters.priceline.priceline_info import PricelineInfo
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.models.hotel_api_model import ImageType
from api.management.commands.simplenight_base_command import SimplenightBaseCommand
from api.models.models import ProviderImages


class PricelineImageParser:
    def __init__(self, transport=None):
        self.adapter_info = PricelineInfo()
        self.provider = self.adapter_info.get_or_create_provider_id()

        self.transport = transport
        if self.transport is None:
            self.transport = PricelineTransport(test_mode=True)

    def parse_and_save(self, pagination_limit=5, limit=None):
        existing_images = ProviderImages.objects.filter(provider=self.provider)

        logger.info(f"Removing {existing_images.count()} existing Priceline images")
        existing_images.delete()

        total_persisted = 0
        initial_results = self._download_images(limit=pagination_limit)
        total_persisted += self._bulk_save_provider_images(initial_results["photos"])

        resume_key = initial_results["resume_key"]
        while resume_key and (limit is None or total_persisted < limit):
            try:
                SimplenightBaseCommand.mock_organization()
                results = self._download_images(resume_key=resume_key, limit=pagination_limit)
                resume_key = results["resume_key"]
                total_persisted += self._bulk_save_provider_images(results["photos"])
                logger.info(f"Persisted {total_persisted} photos")
            except Exception:
                logger.exception("Error downloading images")

    def _download_images(self, limit, resume_key=None):
        response = self.transport.photos_download(resume_key=resume_key, limit=limit, image_size="large")
        return response["getSharedBOF2.Downloads.Hotel.Photos"]["results"]

    def _bulk_save_provider_images(self, provider_images):
        models = list(map(self._create_provider_image_model, provider_images))
        ProviderImages.objects.bulk_create(models)

        return len(models)

    def _create_provider_image_model(self, result):
        url = result["photo_url"]
        url = url.replace("http://", "//")
        url = url.replace("/max500/", "/max2000/")

        return ProviderImages(
            provider=self.provider,
            provider_code=result["hotelid_ppn"],
            type=ImageType.UNKNOWN,
            display_order=result["display_order"],
            image_url=url,
        )
