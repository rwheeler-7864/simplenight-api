import json
from api import logger
from api.hotel.adapters.hotelbeds.hotelbeds_adapter import HotelbedsAdapter
from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.adapters.hotelbeds.hotelbeds_common_models import HOTELBEDS_LANGUAGE_MAP, get_language_mapping, get_thumbnail_url, get_image_url, get_star_rating, safeget
from api.hotel.adapters.hotelbeds.hotelbeds_amenity_mappings import get_simplenight_amenity_mappings
from api.hotel.parsers import hotelbeds_loader
from api.models.models import ProviderHotel, ProviderCity, ProviderImages, ProviderChain

COUNTRY_FILE_PATH = "resources/hotelbeds/hotelbeds_countries_en.json"
with open(COUNTRY_FILE_PATH, "r") as f:
    data = json.load(f)
    country_data = data["countries"]


def get_state_by_code(country_code, state_code):
    country = next(c for c in country_data if c["code"] == country_code)
    if not country:
        return (country_code, state_code)
    state = next(s for s in country["states"] if s["code"] == state_code)
    if not state:
        return (country["isoCode"], state_code)
    return (country["isoCode"], state["name"])


class HotelbedsDetailsParser:
    def __init__(self, transport: HotelbedsTransport):
        self.transport = transport
        self.hotelbeds = HotelbedsAdapter(transport=transport)
        self.provider = self.hotelbeds.adapter_info.get_or_create_provider_id()

        chains = ProviderChain.objects.filter(provider=self.provider)
        self.chains_map = {x.provider_code: x.chain_name for x in chains}

    def load(self, chunk_size=1000, limit=None):
        num_loaded = 0

        for language_code in HOTELBEDS_LANGUAGE_MAP.keys():
            chunked_hotel_data = hotelbeds_loader.load_data(
                self.transport, HotelbedsTransport.Endpoint.HOTEL_CONTENT, chunk_size=chunk_size,
                showFullPortfolio=True, useSecondaryLanguage=False, language=get_language_mapping(language_code)
            )

            for chunk in chunked_hotel_data:
                hotels = []
                images = []
                for hotel in chunk:
                    hotels.append(self.parse_hotel(hotel, language_code))

                    if language_code == "en":
                        images += self.parse_image(hotel)

                ProviderHotel.objects.bulk_create(hotels)
                if len(images) > 0:
                    ProviderImages.objects.bulk_create(images)

                num_loaded += len(hotels)
                logger.info(f"Loaded {num_loaded} hotels")

                if limit and num_loaded >= limit:
                    logger.info(f"Limit reached ({num_loaded} of {limit}). Exiting.")
                    return

    @classmethod
    def remove_old_data(cls):
        # remove hotels
        existing_hotels = ProviderHotel.objects.filter(provider__name=HotelbedsAdapter.get_provider_name())
        logger.info(f"Removing {existing_hotels.count()} existing hotels")
        existing_hotels.delete()

        # remove images
        existing_images = ProviderImages.objects.filter(provider__name=HotelbedsAdapter.get_provider_name())
        logger.info(f"Removing {existing_images.count()} existing images")
        existing_images.delete()

    def parse_hotel(self, hotel_data, language_code):
        country_code, state = get_state_by_code(hotel_data["countryCode"], hotel_data["stateCode"])
        latitude, longitude = self.get_coordinates(hotel_data)
        chain_code, chain_name = self.get_chain(hotel_data)

        return ProviderHotel(
            provider=self.provider,
            language_code=language_code,
            provider_code=hotel_data["code"],
            hotel_name=hotel_data["name"]["content"],
            city_name=hotel_data["city"]["content"],
            state=state,
            country_code=country_code,
            address_line_1=hotel_data["address"]["content"],
            postal_code=hotel_data.get("postalCode", None),
            latitude=latitude,
            longitude=longitude,
            thumbnail_url=self.get_hotel_thumbnail_image(hotel_data),
            star_rating=get_star_rating(hotel_data["categoryCode"]),
            property_description=safeget(hotel_data, "description", "content"),
            amenities=self.get_amenities(hotel_data),
            chain_code=chain_code,
            chain_name=chain_name,
        )

    def parse_image(self, hotel_data):
        if "images" not in hotel_data:
            return []

        return [
            ProviderImages(
                provider=self.provider,
                provider_code=hotel_data["code"],
                type=image["imageTypeCode"],
                display_order=image["visualOrder"],
                image_url=get_image_url(image["path"]),
                meta_info={
                    "room_code": image.get("roomCode", None),
                    "room_type": image.get("roomType", None),
                }
            ) for image in hotel_data["images"]
        ]

    def get_hotel_thumbnail_image(self, hotel_data):
        if "images" not in hotel_data:
            return None
        return get_thumbnail_url(hotel_data["images"])

    def get_amenities(self, hotel_data):
        if "facilities" not in hotel_data:
            return
        return list(set([item["facilityCode"] for item in hotel_data["facilities"]]))

    def get_coordinates(self, hotel_data):
        if "coordinates" not in hotel_data:
            return [None, None]
        return [hotel_data["coordinates"]["latitude"], hotel_data["coordinates"]["longitude"]]

    def get_chain(self, hotel_data):
        if "chainCode" not in hotel_data:
            return [None, None]
        return [hotel_data["chainCode"], self.chains_map.get(hotel_data["chainCode"], None)]
