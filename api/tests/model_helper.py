import uuid
from datetime import date, datetime
from decimal import Decimal

from api.hotel.models.hotel_api_model import ImageType
from api.hotel.models.hotel_common_models import BookingStatus
from api.models.models import (
    Geoname,
    GeonameAlternateName,
    ProviderCity,
    Provider,
    CityMap,
    Airport,
    ProviderHotel,
    Traveler,
    Booking,
    HotelBooking,
    RecordLocator,
    ProviderImages,
)


def create_geoname(geoname_id, location_name, province, country_code, population=0, latitude=None, longitude=None):
    if latitude is None:
        latitude = 50.0

    if longitude is None:
        longitude = 50.0

    geoname = Geoname(
        geoname_id=geoname_id,
        location_name=location_name,
        province=province,
        iso_country_code=country_code,
        latitude=latitude,
        longitude=longitude,
        population=population,
        timezone="US/Pacific",
    )

    geoname.save()
    return geoname


def create_geoname_altname(pk_id, geoname, lang_code, name, is_preferred=False):
    alternate_name = GeonameAlternateName(
        alternate_name_id=pk_id,
        geoname=geoname,
        geoname_id=geoname.geoname_id,
        iso_language_code=lang_code,
        name=name,
        is_colloquial=False,
        is_short_name=False,
        is_preferred=is_preferred,
    )

    alternate_name.save()
    return alternate_name


def create_provider(provider_name: str):
    return Provider.objects.get_or_create(name=provider_name)[0]


def create_provider_city(
    provider_name: str,
    code: str,
    name: str,
    province: str,
    country: str,
    latitude: float = None,
    longitude: float = None,
):
    if latitude is None:
        latitude = 0.0
        longitude = 0.0

    provider = Provider.objects.get(name=provider_name)
    provider_city = ProviderCity(
        provider=provider,
        provider_code=code,
        location_name=name,
        province=province,
        country_code=country,
        latitude=latitude,
        longitude=longitude,
    )

    provider_city.save()
    return provider_city


def create_city_mapping(provider_name: str, simplenight_id: str, provider_id: str):
    provider = Provider.objects.get(name=provider_name)
    city_mapping = CityMap(provider=provider, simplenight_city_id=simplenight_id, provider_city_id=provider_id)
    city_mapping.save()

    return city_mapping


def create_airport(airport_id, airport_code, airport_name):
    airport = Airport(
        airport_id=airport_id, airport_code=airport_code, airport_name=airport_name, latitude=50.0, longitude=50.0
    )

    airport.save()
    return airport


def create_provider_hotel(provider, provider_code, hotel_name):
    provider_hotel = ProviderHotel(
        provider=provider,
        hotel_name=hotel_name,
        address_line_1="123 Simple Way",
        provider_code=provider_code,
        city_name="Simpleville",
    )

    provider_hotel.save()
    return provider_hotel


def create_provider_image(provider, provider_code, url):
    ProviderImages.objects.create(
        provider=provider, provider_code=provider_code, image_url=url, display_order=1, type=ImageType.UNKNOWN
    )


def create_traveler(first_name="John", last_name="Simplenight"):
    traveler = Traveler(
        first_name=first_name, last_name=last_name, email_address="john.simplenight@foo.bar", phone_number="5558675309",
    )

    traveler.save()
    return traveler


def create_booking(booking_date=None, traveler=None, organization=None):
    if booking_date is None:
        booking_date = datetime.now()

    if traveler is None:
        traveler = Traveler(
            first_name="John",
            last_name="Simplenight",
            country="US",
            province="CA",
            address_line_1="123 Simple Way",
            email_address="johnsimplenight@simplenight.com",
            phone_number="5558675309",
        )
        traveler.save()

    booking = Booking.objects.create(
        transaction_id=str(uuid.uuid4()),
        lead_traveler=traveler,
        booking_date=booking_date,
        booking_status=BookingStatus.BOOKED.value,
        organization=organization,
    )

    RecordLocator.generate_record_locator(booking)

    return booking


def create_hotel_booking(booking, hotel_name, hotel_id, sn_hotel_id, provider, hotel_record_locator):
    return HotelBooking.objects.create(
        hotel_name=hotel_name,
        provider=provider,
        booking=booking,
        provider_total=Decimal("100.0"),
        provider_currency="USD",
        total_price=Decimal("113.0"),
        currency="USD",
        record_locator=hotel_record_locator,
        checkin=date(2020, 1, 1),
        checkout=date(2020, 1, 7),
        provider_hotel_id=hotel_id,
        simplenight_hotel_id=sn_hotel_id,
    )
