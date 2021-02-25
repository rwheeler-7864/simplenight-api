from api import logger
from api.hotel.adapters.priceline.priceline_adapter import PricelineAdapter
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.parsers import priceline_loader
from api.models.models import ProviderHotel


class PricelineDetailsParser:
    def __init__(self, transport: PricelineTransport):
        self.transport = transport
        self.priceline = PricelineAdapter(transport=transport)
        self.provider = self.priceline.adapter_info.get_or_create_provider_id()

    def load(self, chunk_size=10000, limit=None):
        num_loaded = 0
        chunked_hotel_data = priceline_loader.load_data(
            self.transport, PricelineTransport.Endpoint.HOTELS_DOWNLOAD, chunk_size=chunk_size
        )

        for chunk in chunked_hotel_data:
            models = list(map(self.parse_hotel, chunk))
            ProviderHotel.objects.bulk_create(models)

            num_loaded += len(models)
            logger.info(f"Loaded {num_loaded} hotels")

            if limit and num_loaded >= limit:
                logger.info(f"Limit reached ({num_loaded} of {limit}). Exiting.")
                return

    @classmethod
    def remove_old_data(cls):
        existing_records = ProviderHotel.objects.filter(provider__name=PricelineAdapter.get_provider_name())

        logger.info(f"Removing {existing_records.count()} existing records")
        existing_records.delete()

    def parse_hotel(self, hotel_data):

        amenities = []
        amenities_response = hotel_data["amenity_codes"]
        if amenities_response:
            amenities = amenities_response.split("^")

        return ProviderHotel(
            provider=self.provider,
            language_code="en",
            provider_code=hotel_data["hotelid_ppn"],
            hotel_name=hotel_data["hotel_name"],
            city_name=hotel_data["city"],
            state=hotel_data["state"],
            country_code=hotel_data["country_code"],
            address_line_1=hotel_data["hotel_address"],
            postal_code=hotel_data["postal_code"],
            latitude=hotel_data["latitude"],
            longitude=hotel_data["longitude"],
            thumbnail_url=hotel_data["thumbnail"],
            star_rating=hotel_data["star_rating"],
            property_description=hotel_data["property_description"],
            amenities=amenities,
            provider_reference=self.transport.priceline_refid,
        )
