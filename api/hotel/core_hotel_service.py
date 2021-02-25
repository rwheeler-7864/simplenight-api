import uuid
from copy import copy
from datetime import datetime
from decimal import Decimal, ROUND_UP, getcontext
from functools import wraps
from typing import List, Union, Tuple, Callable, Optional

from api import logger
from api.common import analytics, request_context
from api.hotel import markups, provider_cache_service, hotel_mappings
from api.hotel.adapters import adapter_service, adapter_common
from api.hotel.adapters.hotel_adapter import HotelAdapter
from api.hotel.models.adapter_models import AdapterHotelSearch, AdapterOccupancy, AdapterHotelBatchSearch
from api.hotel.models.hotel_api_model import (
    HotelDetails,
    HotelSpecificSearch,
    AdapterHotel,
    HotelLocationSearch,
    HotelDetailsSearchRequest,
    Hotel,
    HotelSearch,
    Image,
    ImageType,
    HotelBatchSearch,
)
from api.hotel.models.hotel_common_models import RoomRate, HotelReviews
from api.models.models import ProviderImages, ProviderMapping, SearchType, SearchResult
from api.view.exceptions import SimplenightApiException, AvailabilityException, AvailabilityErrorCode


def record_search_event(f):
    @wraps(f)
    def wrapper(search: HotelSearch):
        begin_time = datetime.now()
        search_event_data_id = str(uuid.uuid4())
        search_result = SearchResult.FAILURE
        try:
            result = f(search, search_id=search_event_data_id)
            search_result = SearchResult.SUCCESS
            return result
        finally:
            end_time = datetime.now()
            elapsed_time = int((end_time - begin_time).total_seconds() * 1000)
            logger.info(f"Search Result = {search_result.name}, elapsed time = {elapsed_time}")
            _record_search_event(
                search=search, search_id=search_event_data_id, result=search_result, elapsed_time=elapsed_time
            )

    return wrapper


@record_search_event
def search_by_location(search_request: HotelLocationSearch, search_id: str = None) -> List[Hotel]:
    all_hotels = _search_all_adapters(search_request, HotelAdapter.search_by_location)
    return _process_hotels(all_hotels, search_id=search_id)


@record_search_event
def search_by_id(search_request: HotelSpecificSearch, search_id: str = None) -> Hotel:
    adapters = adapter_service.get_hotel_adapters_to_search(search_request)
    adapter_name = adapters[0].get_provider_name()
    adapter_search_request = _adapter_search_request(search_request, adapter_name)

    if len(adapters) > 1:
        raise SimplenightApiException("More than one adapter specified in hotel specific search", 500)

    try:
        hotel = adapters[0].search_by_id(adapter_search_request)
        return _process_hotels(hotel, search_id=search_id)
    except AvailabilityException as e:
        raise e
    except Exception:
        logger.exception(f"Error processing {adapter_name}")
        message = f"Error: Exception while processing adapter {adapter_name}"
        raise AvailabilityException(message, error_type=AvailabilityErrorCode.PROVIDER_ERROR)


@record_search_event
def search_by_id_batch(search_request: HotelBatchSearch, search_id: str = None) -> List[Hotel]:
    adapters = adapter_service.get_hotel_adapters_to_search(search_request)
    adapter_name = adapters[0].get_provider_name()
    adapter_search_request = _adapter_batch_hotel_id_search_request(search_request, adapter_name)

    try:
        hotel = adapters[0].search_by_id_batch(adapter_search_request)
        return _process_hotels(hotel, search_id=search_id)
    except AvailabilityException as e:
        logger.error(f"Could not find availability: {str(e)}")
        return []
    except Exception:
        logger.exception(f"Error processing {adapter_name}")
        raise AvailabilityException(
            f"Error: Exception while processing adapter {adapter_name}", error_type=AvailabilityErrorCode.PROVIDER_ERROR
        )


def details(hotel_details_req: HotelDetailsSearchRequest) -> HotelDetails:
    adapter = adapter_service.get_adapters(hotel_details_req.provider)[0]
    return adapter.details(hotel_details_req)


def recheck(provider: str, room_rate: RoomRate) -> RoomRate:
    adapter = adapter_service.get_adapter(provider)
    return adapter.recheck(room_rate)


def reviews(simplenight_hotel_id: str) -> HotelReviews:
    adapter = adapter_service.get_adapter("priceline")  # TODO: Make this work for any provider
    provider_hotel_code = hotel_mappings.find_provider_hotel_id(simplenight_hotel_id, "priceline")

    return adapter.reviews(hotel_id=provider_hotel_code)


def _search_all_adapters(search_request: HotelSearch, adapter_fn: Callable):
    adapters = adapter_service.get_hotel_adapters_to_search(search_request)

    hotels = []
    for adapter in adapters:
        adapter_fn_name = getattr(adapter, adapter_fn.__name__)
        hotels.extend(adapter_fn_name(search_request))

    return hotels


def _process_hotels(adapter_hotels: Union[List[AdapterHotel], AdapterHotel], search_id) -> Union[Hotel, List[Hotel]]:
    """
    Given an AdapterHotel, calculate markups, minimum nightly rates
    and return a Hotel object suitable for the API view layer
    """

    if isinstance(adapter_hotels, AdapterHotel):
        return _process_hotel(adapter_hotels, search_id=search_id)

    return list(filter(lambda x: x is not None, map(lambda x: _process_hotel(x, search_id=search_id), adapter_hotels)))


def _process_hotel(adapter_hotel: AdapterHotel, search_id: str = None) -> Optional[Hotel]:
    simplenight_hotel_id = hotel_mappings.find_simplenight_hotel_id(
        provider_hotel_id=adapter_hotel.hotel_id, provider_name=adapter_hotel.provider
    )

    if not simplenight_hotel_id:
        logger.warn(f"Skipping {adapter_hotel.provider} hotel {adapter_hotel.hotel_id} because no SN mapping found")
        return None

    lowest_provider_rate = copy(_calculate_hotel_min_rates(adapter_hotel))

    _markup_room_rates(adapter_hotel)
    _enrich_hotels(adapter_hotel)
    average_nightly_base, average_nightly_tax, average_nightly_rate = _calculate_hotel_min_nightly_rates(adapter_hotel)

    lowest_simplenight_rate = _calculate_hotel_min_rates(adapter_hotel)
    analytics.add_hotel_event(
        search_event_data_id=search_id,
        provider=adapter_common.get_provider(adapter_hotel.provider),
        provider_code=adapter_hotel.hotel_id,
        giata_code=simplenight_hotel_id,
        total=lowest_simplenight_rate.total.amount,
        base=lowest_simplenight_rate.total_base_rate.amount,
        taxes=lowest_simplenight_rate.total_tax_rate.amount,
        provider_total=lowest_provider_rate.total.amount,
        provider_base=lowest_provider_rate.total_base_rate.amount,
        provider_taxes=lowest_provider_rate.total_tax_rate.amount,
    )

    return Hotel(
        hotel_id=simplenight_hotel_id,
        start_date=adapter_hotel.start_date,
        end_date=adapter_hotel.end_date,
        occupancy=adapter_hotel.occupancy,
        hotel_details=adapter_hotel.hotel_details,
        room_types=adapter_hotel.room_types,
        room_rates=adapter_hotel.room_rates,
        rate_plans=adapter_hotel.rate_plans,
        average_nightly_rate=average_nightly_rate,
        average_nightly_base=average_nightly_base,
        average_nightly_tax=average_nightly_tax,
    )


def _enrich_hotels(adapter_hotel: AdapterHotel):
    provider_name = adapter_hotel.provider
    provider_code = adapter_hotel.hotel_id
    try:
        provider_mapping = _get_provider_mapping(provider_name, provider_code=provider_code)
        _enrich_images(adapter_hotel, provider_mapping)
    except Exception:
        logger.exception("Error while enriching hotel")


def _enrich_images(adapter_hotel: AdapterHotel, provider_mapping: ProviderMapping):
    if not provider_mapping:
        return

    iceportal_images = _get_iceportal_images_from_provider_code(provider_mapping)
    if iceportal_images:
        iceportal_images = list(map(_convert_image, iceportal_images))
        adapter_hotel.hotel_details.thumbnail_url = iceportal_images[0].url
        adapter_hotel.hotel_details.photos = iceportal_images


def _get_iceportal_images_from_provider_code(provider_mapping: ProviderMapping):
    iceportal_mapping = _get_provider_mapping("iceportal", giata_code=provider_mapping.giata_code)

    if not iceportal_mapping:
        return []

    images = ProviderImages.objects.filter(provider__name="iceportal", provider_code=iceportal_mapping.provider_code)
    images.order_by("display_order")

    return images


def _get_provider_mapping(provider_name, provider_code=None, giata_code=None):
    try:
        if giata_code:
            provider_mapping = ProviderMapping.objects.get(provider__name=provider_name, giata_code=giata_code)
        elif provider_code:
            provider_mapping = ProviderMapping.objects.get(provider__name=provider_name, provider_code=provider_code)
        else:
            raise ValueError("Must provide provider_code or giata_code")

        logger.debug(f"Found provider mapping: {provider_mapping}")
        return provider_mapping
    except ProviderMapping.DoesNotExist:
        logger.info(f"Could not find mapping info for provider hotel: {provider_name}/{provider_code}")


def _convert_image(provider_image: ProviderImages):
    return Image(url=provider_image.image_url, type=ImageType.UNKNOWN, display_order=provider_image.display_order)


def _markup_room_rates(hotel: AdapterHotel):
    room_rates = []
    for provider_rate in hotel.room_rates:
        simplenight_rate = markups.markup_rate(provider_rate)
        provider_cache_service.save_provider_rate(hotel, provider_rate, simplenight_rate)
        room_rates.append(simplenight_rate)

    hotel.room_rates = room_rates


def _get_nightly_rate(hotel: Union[Hotel, AdapterHotel], amount: Decimal):
    room_nights = max((hotel.end_date - hotel.start_date).days, 1)

    getcontext().rounding = ROUND_UP
    return Decimal(round(amount / room_nights, 2))


def _calculate_hotel_min_nightly_rates(hotel: Union[Hotel, AdapterHotel]) -> Tuple[Decimal, Decimal, Decimal]:
    least_cost_rate = _calculate_hotel_min_rates(hotel)

    min_nightly_total = _get_nightly_rate(hotel, least_cost_rate.total.amount)
    min_nightly_tax = _get_nightly_rate(hotel, least_cost_rate.total_tax_rate.amount)
    min_nightly_base = _get_nightly_rate(hotel, least_cost_rate.total_base_rate.amount)

    return min_nightly_base, min_nightly_tax, min_nightly_total


def _calculate_hotel_min_rates(hotel: Union[Hotel, AdapterHotel]) -> RoomRate:
    return min(hotel.room_rates, key=lambda x: x.total.amount)


def _adapter_search_request(search: HotelSpecificSearch, provider_name: str) -> AdapterHotelSearch:
    provider_hotel_id = hotel_mappings.find_provider_hotel_id(search.hotel_id, provider_name)
    if not provider_hotel_id:
        raise AvailabilityException(
            detail="Provider hotel mapping not found", error_type=AvailabilityErrorCode.HOTEL_NOT_FOUND
        )

    occupancy = AdapterOccupancy(
        adults=search.occupancy.adults, children=search.occupancy.children, num_rooms=search.occupancy.num_rooms
    )

    return AdapterHotelSearch(
        start_date=search.start_date,
        end_date=search.end_date,
        occupancy=occupancy,
        language=search.language,
        currency=search.currency,
        provider_hotel_id=provider_hotel_id,
        simplenight_hotel_id=search.hotel_id,
    )


def _adapter_batch_hotel_id_search_request(search: HotelBatchSearch, provider_name: str) -> AdapterHotelBatchSearch:
    hotel_ids = search.hotel_ids
    simplenight_to_provider_map = hotel_mappings.find_simplenight_to_provider_map(provider_name, hotel_ids)
    if len(simplenight_to_provider_map) == 0:
        raise AvailabilityException(
            "Could not find any mapped hotels to search in batch", AvailabilityErrorCode.HOTEL_NOT_FOUND
        )

    unmatched_hotel_ids = set(hotel_ids) - set(simplenight_to_provider_map.keys())
    logger.info(f"Created adapter batch search for {provider_name}. Unmatched IDs = {unmatched_hotel_ids}")

    occupancy = AdapterOccupancy(
        adults=search.occupancy.adults, children=search.occupancy.children, num_rooms=search.occupancy.num_rooms
    )

    return AdapterHotelBatchSearch(
        start_date=search.start_date,
        end_date=search.end_date,
        occupancy=occupancy,
        language=search.language,
        currency=search.currency,
        simplenight_hotel_ids=list(simplenight_to_provider_map.keys()),
        provider_hotel_ids=list(simplenight_to_provider_map.values()),
    )


# noinspection PyTypeChecker
def _record_search_event(search: HotelSearch, search_id: str, result: SearchResult, elapsed_time: int):
    def get_request_id():
        request_id = request_context.get_request_context().get_request_id()
        if request_id:
            return request_id[:8]

    search_types = {
        HotelLocationSearch: SearchType.HOTEL_BY_LOCATION,
        HotelSpecificSearch: SearchType.HOTEL_BY_ID,
        HotelBatchSearch: SearchType.HOTEL_BY_BATCH,
    }

    search_type = search_types.get(search.__class__)
    analytics.add_search_event(
        search_id=search_id,
        search_type=search_type,
        start_date=search.start_date,
        end_date=search.end_date,
        search_input=_get_search_input(search),
        search_result=result,
        elapsed_time=elapsed_time,
        request_id=get_request_id(),
    )


def _get_search_input(search: HotelSearch):
    if isinstance(search, HotelLocationSearch):
        return search.location_id
    elif isinstance(search, HotelSpecificSearch):
        return search.hotel_id
    elif isinstance(search, HotelBatchSearch):
        return str.join(",", search.hotel_ids or [])
