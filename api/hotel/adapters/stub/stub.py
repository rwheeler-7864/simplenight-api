import decimal
import random
import uuid
from datetime import timedelta
from typing import List

from api.hotel import provider_cache_service
from api.hotel.adapters.hotel_adapter import HotelAdapter
from api.hotel.models.adapter_models import (
    AdapterLocationSearch,
    AdapterBaseSearch,
    AdapterCancelRequest,
    AdapterCancelResponse,
    AdapterHotelBatchSearch,
)
from api.hotel.models.booking_model import HotelReservation, Locator, AdapterHotelBookingRequest
from api.hotel.models.hotel_api_model import (
    AdapterHotel,
    RoomType,
    Image,
    ImageType,
    BedTypes,
    CancellationPolicy,
    HotelDetails,
    GeoLocation,
    RatePlan,
    HotelSearch,
    HotelSpecificSearch,
    SimplenightAmenities,
    CancellationSummary,
)
from api.hotel.models.hotel_common_models import RoomOccupancy, Address, RateType, Money, RoomRate, HotelReviews
from api.tests.utils import random_alphanumeric
from common.utils import random_string


class StubHotelAdapter(HotelAdapter):
    """Stub Hotel Adapter, generates fakes data, for testing purposes"""

    PROVIDER_NAME = "stub_hotel"

    def search_by_location(self, search: AdapterLocationSearch) -> List[AdapterHotel]:
        num_hotels_to_return = random.randint(10, 50)
        hotels = [self.search_by_id(search) for _ in range(num_hotels_to_return)]

        return hotels

    def search_by_id(self, search_request: AdapterBaseSearch) -> AdapterHotel:
        hotel_code = random_string(5).upper()
        if isinstance(search_request, HotelSpecificSearch) and search_request.hotel_id:
            hotel_code = search_request.hotel_id

        room_types = self._generate_room_types()
        rate_plans = self._generate_rate_plans(search_request)
        room_rates = self._generate_room_rates(room_types, rate_plans)

        response = AdapterHotel(
            provider=self.PROVIDER_NAME,
            hotel_id=hotel_code,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            occupancy=RoomOccupancy(adults=2, children=2),
            room_types=room_types,
            rate_plans=rate_plans,
            room_rates=room_rates,
            hotel_details=self._generate_hotel_details(),
        )

        return response

    def search_by_id_batch(self, search_request: AdapterHotelBatchSearch) -> List[AdapterHotel]:
        raise NotImplementedError("Search by ID Batch Not Implemented")

    def recheck(self, room_rate: RoomRate) -> RoomRate:
        return room_rate

    def details(self, *args):
        return self._generate_hotel_details(city="Foo")

    def reviews(self, *args) -> HotelReviews:
        raise NotImplementedError()

    def booking_availability(self, search_request: AdapterBaseSearch):
        return self.search_by_id(search_request)

    def book(self, book_request: AdapterHotelBookingRequest) -> HotelReservation:
        cached_room_data = provider_cache_service.get_simplenight_rate(book_request.room_code)
        return HotelReservation(
            locator=Locator(id=str(uuid.uuid4())),
            hotel_locator=[Locator(id=random_alphanumeric(6))],
            hotel_id=cached_room_data.hotel_id,
            checkin=cached_room_data.checkin,
            checkout=cached_room_data.checkout,
            customer=book_request.customer,
            traveler=book_request.traveler,
            room_rate=cached_room_data.simplenight_rate,
        )

    def cancel(self, cancel_request: AdapterCancelRequest) -> AdapterCancelResponse:
        raise NotImplementedError("Cancel not implemented")

    def _generate_room_types(self):
        bed_types = {
            "King": BedTypes(king=1),
            "Queen": BedTypes(queen=random.randint(1, 2)),
            "Double": BedTypes(double=random.randint(1, 2)),
            "Single": BedTypes(single=random.randint(1, 2)),
        }

        room_category = [
            "Ocean View",
            "Garden View",
            "City View",
            "Run of the House",
            "Superior Room",
            "Deluxe Room",
            "Junior Suite",
            "Prestige Suite",
        ]

        room_types = []
        for i in range(random.randint(1, 4)):
            code = random_string(6).upper()
            bed_type = random.choice([x for x in bed_types.keys()])
            category = random.choice(room_category)
            room_type_name = f"{bed_type} Bed {category}"
            amenities = random.sample(list(SimplenightAmenities), random.randint(1, 2))
            photos = self._get_photos(code)

            description = f"{category} room with a {bed_type.lower()} bed"
            room_type = RoomType(
                code=code,
                name=room_type_name,
                description=description,
                amenities=amenities,
                photos=photos,
                capacity=RoomOccupancy(adults=random.randint(0, 2), children=2),
                bed_types=bed_types[bed_type],
            )

            room_types.append(room_type)

        return room_types

    @staticmethod
    def _generate_rate_plans(hotel_search: HotelSearch):
        penalty_date = hotel_search.start_date - timedelta(days=14)
        cancellation_message = f"Free Cancellation allowed without charge before {penalty_date}"
        refundable_rate_plan = RatePlan(
            name="Free Cancellation",
            code=random_alphanumeric(8),
            description=cancellation_message,
            amenities=[SimplenightAmenities.WIFI],
            cancellation_policy=CancellationPolicy(
                summary=CancellationSummary.FREE_CANCELLATION,
                cancellation_deadline=hotel_search.start_date - timedelta(days=14),
            ),
        )

        non_refundable_rate_plan = RatePlan(
            name="Lowest Rate",
            code=random_alphanumeric(8),
            description=f"Lowest available rate (non-refundable)",
            amenities=[],
            cancellation_policy=CancellationPolicy(summary=CancellationSummary.NON_REFUNDABLE),
        )

        return [refundable_rate_plan, non_refundable_rate_plan]

    @staticmethod
    def _generate_room_rates(room_types: List[RoomType], rate_plan_types: List[RatePlan]):
        room_rates = []
        for room_types in room_types:
            for rate_plan in rate_plan_types:
                total_rate = round(decimal.Decimal(random.random() * 1200), 2)
                total_tax_rate = round(decimal.Decimal(total_rate / 10), 2)
                total_base_rate = decimal.Decimal(total_rate - total_tax_rate)

                room_rates.append(
                    RoomRate(
                        code=random_alphanumeric(8),
                        room_type_code=room_types.code,
                        rate_plan_code=rate_plan.code,
                        maximum_allowed_occupancy=RoomOccupancy(adults=2, children=2),
                        total_base_rate=Money(amount=total_base_rate, currency="USD"),
                        total_tax_rate=Money(amount=total_tax_rate, currency="USD"),
                        total=Money(amount=total_rate, currency="USD"),
                        rate_type=RateType.BOOKABLE,
                    )
                )

        return room_rates

    def _generate_hotel_details(self, city=None):
        hotel_brands = ["Marriott", "Westin", "St. Regis", "Hyatt", "Holiday Inn"]
        hotel_location = ["Oceanfront", "Beach", "Garden", "Boardwalk", "Downtown"]
        hotel_types = ["Suites", "Cottages", "Tower", "Villas", "Inn"]

        random_brand = random.choice(hotel_brands)
        random_location = random.choice(hotel_location)
        random_type = random.choice(hotel_types)

        hotel_name = f"{random_brand} {random_location} {random_type}"
        hotel_address = self._generate_address(city=city)
        hotel_code = random_string(5).upper()

        latitude = random.random() * 100
        longitude = random.random() * 100
        geolocation = GeoLocation(latitude=latitude, longitude=longitude)

        star_rating = random.choice([2, 2.5, 3, 3.5, 4, 4.5, 5])
        review_rating = random.choice([10.0])

        amenities = random.sample(list(SimplenightAmenities), random.randint(3, 10))

        return HotelDetails(
            name=hotel_name,
            address=hotel_address,
            chain_code="1A",
            hotel_code=hotel_code,
            checkin_time="3PM",
            checkout_time="12PM",
            geolocation=geolocation,
            photos=[],
            amenities=amenities,
            star_rating=star_rating,
            review_rating=review_rating,
            property_description=self._get_property_description(),
        )

    @staticmethod
    def _generate_address(city=None):
        cities = ["San Francisco", "New York", "Seattle", "Los Angeles", "Boston"]
        street_types = ["Street", "Way", "Place", "Loop", "Boulevard"]
        street_names = ["Market", "Park", "Broadway", "First", "Second"]
        random_address = random.randrange(1, 1000, 8)
        random_type = random.choice(street_types)
        random_name = random.choice(street_names)

        if city is None:
            city = random.choice(cities)

        random_street_address = f"{random_address} {random_name} {random_type}"

        return Address(city=city, province="CA", country="US", postal_code="12345", address1=random_street_address)

    @staticmethod
    def _get_photos(code):
        photos = []
        for i in range(random.randint(1, 10)):
            url = f"https://i.simplenight-api-278418.ue.r.appspot.com/i/{code}.{i}.jpg"
            photos.append(Image(url=url, type=ImageType.ROOM))

        return photos

    @staticmethod
    def _get_property_description():
        return "This is the property description."

    @classmethod
    def factory(cls, test_mode=True):
        return StubHotelAdapter()

    @classmethod
    def get_provider_name(cls):
        return cls.PROVIDER_NAME
