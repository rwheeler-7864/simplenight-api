from datetime import timedelta
from decimal import Decimal
from typing import Union, Dict, List

from api import logger
from api.hotel import hotel_service
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.google_pricing import google_pricing_serializer
from api.hotel.google_pricing.google_pricing_models import GooglePricingItineraryQuery
from api.hotel.models.hotel_api_model import (
    HotelBatchSearch,
    SimplenightHotel,
    HotelDetails,
    GeoLocation,
    SimplenightRoomType,
    CancellationPolicy,
    CancellationSummary,
)
from api.hotel.models.hotel_common_models import RoomOccupancy, Address, Money, RateType
from api.models.models import ProviderHotel, ProviderMapping
from api.view.exceptions import AvailabilityException, AvailabilityErrorCode


def live_pricing_api(query: Union[str, bytes, GooglePricingItineraryQuery]) -> str:
    if isinstance(query, (str, bytes)):
        query = google_pricing_serializer.deserialize(query)

    checkout = query.checkin + timedelta(days=query.nights)
    occupancy = RoomOccupancy(adults=2)
    search = HotelBatchSearch(
        start_date=query.checkin, end_date=checkout, occupancy=occupancy, hotel_ids=query.hotel_codes, currency="USD"
    )

    try:
        hotel_availability = hotel_service.search_by_id_batch(search)
        hotel_availability_by_hotel_code = {hotel.hotel_id: hotel for hotel in hotel_availability}
    except AvailabilityException as e:
        logger.info(f"Error while searching Google Live Pricing: {str(e)}")
        hotel_availability_by_hotel_code = {}
    except Exception:
        logger.exception(f"Error while searching Google Live Pricing")
        hotel_availability_by_hotel_code = {}

    # If a hotel is not returned by the Adapter, we still want to return the property
    # we return the base rate as -1 if no availability exists for the dates
    giata_hotel_codes = query.hotel_codes
    giata_hotels = ProviderHotel.objects.filter(provider__name="giata", provider_code__in=giata_hotel_codes)
    giata_hotels_by_hotel_code: Dict[str, SimplenightHotel] = {
        giata_hotel.provider_code: create_hotel_shell(giata_hotel, query.checkin, checkout)
        for giata_hotel in giata_hotels
    }

    for giata_hotel_id, giata_hotel in giata_hotels_by_hotel_code.items():
        if giata_hotel_id in hotel_availability_by_hotel_code:
            availability_hotel = hotel_availability_by_hotel_code[giata_hotel_id]
            logger.info(f"Found Giata hotel with availability!: {giata_hotel_id}")

            giata_hotel.room_types = availability_hotel.room_types
            giata_hotel.occupancy = availability_hotel.occupancy
        else:
            logger.debug(f"Found no availability for Giata hotel: {giata_hotel_id}")
            giata_hotel.room_types = [
                SimplenightRoomType(
                    code="foo",
                    name="lowest_rate",
                    description="lowest_rate",
                    amenities=[],
                    photos=[],
                    capacity=RoomOccupancy(),
                    total=Money(amount=Decimal(-1), currency="USD"),
                    total_tax_rate=Money(amount=Decimal(-1), currency="USD"),
                    total_base_rate=Money(amount=Decimal(-1), currency="USD"),
                    cancellation_policy=CancellationPolicy(summary=CancellationSummary.NON_REFUNDABLE),
                    avg_nightly_rate=Money(amount=Decimal(-1), currency="USD"),
                    rate_type=RateType.RECHECK,
                )
            ]

    hotel_pricing_list = list(giata_hotels_by_hotel_code.values())
    if not hotel_pricing_list:
        raise AvailabilityException("Could not find hotels", AvailabilityErrorCode.HOTEL_NOT_FOUND)

    logger.info(f"Found Availability for {len(giata_hotels_by_hotel_code)}: {giata_hotels_by_hotel_code.keys()}")
    return google_pricing_serializer.serialize(query, hotel_pricing_list)


def generate_property_list(country_codes: str, provider_name="giata"):
    country_codes = country_codes.split(",")
    logger.info(f"Searching for hotels in {country_codes}")

    logger.info("Looking up Priceline hotels, to restrict list of properties to hotels with a Priceline mapping")
    priceline_hotel_codes = ProviderHotel.objects.filter(provider__name=PricelineAdapter.get_provider_name()).values(
        "provider_code"
    )

    logger.info("Looking up provider mappings for Priceline hotels")
    giata_hotel_codes = ProviderMapping.objects.filter(
        provider__name=PricelineAdapter.get_provider_name(), provider_code__in=priceline_hotel_codes
    ).values("giata_code")

    logger.info("Looking up Giata hotels which have a Priceline mapping")
    provider_hotels = ProviderHotel.objects.prefetch_related("phone").filter(
        provider__name=provider_name, country_code__in=country_codes, provider_code__in=giata_hotel_codes
    )

    logger.info(f"Found {len(provider_hotels)} hotels")
    return google_pricing_serializer.serialize_property_list(provider_hotels)


def generate_property_list_hotel_codes(hotel_codes: List[str]):
    logger.info("Looking up Giata hotels for property list")
    provider_hotels = ProviderHotel.objects.prefetch_related("phone").filter(
        provider__name="giata", provider_code__in=hotel_codes
    )

    logger.info(f"Found {len(provider_hotels)} hotels")
    return google_pricing_serializer.serialize_property_list(provider_hotels)


def create_hotel_shell(provider_hotel: ProviderHotel, start_date, end_date) -> SimplenightHotel:
    return SimplenightHotel(
        hotel_details=HotelDetails(
            name=provider_hotel.hotel_name,
            address=Address(
                address1=provider_hotel.address_line_1,
                address2=provider_hotel.address_line_2,
                city=provider_hotel.city_name,
                province=provider_hotel.state,
                postal_code=provider_hotel.postal_code,
                country=provider_hotel.country_code,
            ),
            geolocation=GeoLocation(latitude=provider_hotel.latitude, longitude=provider_hotel.longitude),
            hotel_code=provider_hotel.provider_code,
        ),
        start_date=start_date,
        end_date=end_date,
        hotel_id=provider_hotel.provider_code,
        occupancy=RoomOccupancy(),
    )
