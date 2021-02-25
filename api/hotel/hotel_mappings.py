from typing import Optional, Dict, List

from cachetools.func import ttl_cache

from api import logger
from api.models.models import ProviderMapping, ProviderHotel


@ttl_cache(maxsize=65536, ttl=86400)
def find_provider_hotel_id(simplenight_hotel_id: str, provider_name: str) -> Optional[str]:
    logger.info(f"Finding hotel mappings for {provider_name} using SN ID {simplenight_hotel_id}")

    try:
        mapping = ProviderMapping.objects.get(provider__name=provider_name, giata_code=simplenight_hotel_id)
        logger.info(f"Found mapping {mapping.provider_code}")

        return mapping.provider_code
    except ProviderMapping.DoesNotExist:
        logger.warn(f"Could not find Provider ID for SN ID {simplenight_hotel_id}")


@ttl_cache(maxsize=65536, ttl=86400)
def find_provider_hotel(simplenight_hotel_id: str, provider_name: str) -> Optional[ProviderHotel]:
    provider_code = find_provider_hotel_id(simplenight_hotel_id, provider_name)
    if provider_code:
        logger.info(f"Searching for provider hotel using provider code {provider_code}")

        try:
            provider_hotel = ProviderHotel.objects.get(provider__name=provider_name, provider_code=provider_code)
            logger.info(f"Found provider hotel {provider_hotel.hotel_name}")

            return provider_hotel
        except ProviderHotel.DoesNotExist:
            logger.warn(f"Could not find ProviderHotel for SN ID {simplenight_hotel_id}")


@ttl_cache(maxsize=65536, ttl=86400)
def find_simplenight_hotel_id(provider_hotel_id: str, provider_name: str) -> Optional[str]:
    logger.info(f"Searching for Simplenight hotel ID using {provider_name} ID {provider_hotel_id}")

    try:
        mapping = ProviderMapping.objects.get(provider__name=provider_name, provider_code=provider_hotel_id)
        logger.info(f"Found mapping {mapping.provider_code}")

        return mapping.giata_code
    except ProviderMapping.DoesNotExist:
        logger.warn(f"Could not find Simplenight ID for {provider_name }ID {provider_hotel_id}")


def find_provider_to_simplenight_map(provider_name: str, provider_codes: List[str]) -> Dict[str, str]:
    provider_simplenight_map = ProviderMapping.objects.filter(
        provider__name=provider_name, provider_code__in=provider_codes
    )

    return {x.provider_code: x.giata_code for x in provider_simplenight_map}


def find_simplenight_to_provider_map(provider_name, giata_codes: List[str]) -> Dict[str, str]:
    simplenight_provider_map = ProviderMapping.objects.filter(
        provider__name=provider_name, giata_code__in=giata_codes
    )

    return {x.giata_code: x.provider_code for x in simplenight_provider_map}
