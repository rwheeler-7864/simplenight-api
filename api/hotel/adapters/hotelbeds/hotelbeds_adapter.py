from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import List, Any, Dict

import json
import pytz
from dateutil.relativedelta import relativedelta

from api import logger
from api.hotel.adapters.hotel_adapter import HotelAdapter
from api.hotel.adapters.hotelbeds.hotelbeds_amenity_mappings import get_simplenight_amenity_mappings
from api.hotel.adapters.hotelbeds.hotelbeds_common_models import get_language_mapping, safeget, get_image_type
from api.hotel.adapters.hotelbeds.hotelbeds_info import HotelbedsInfo
from api.hotel.adapters.hotelbeds.hotelbeds_transport import HotelbedsTransport
from api.hotel.models.adapter_models import (
    AdapterLocationSearch,
    AdapterBaseSearch,
    AdapterHotelSearch,
    AdapterCancelRequest,
    AdapterCancelResponse,
    AdapterHotelBatchSearch,
)
from api.hotel.models.booking_model import (
    HotelReservation,
    Locator,
    AdapterHotelBookingRequest,
)
from api.hotel.models.hotel_api_model import (
    HotelDetails,
    AdapterHotel,
    RoomType,
    RatePlan,
    CancellationPolicy,
    CancellationSummary,
    CancellationDetails,
    Image,
    ImageType,
    GeoLocation,
)
from api.hotel.models.hotel_common_models import (
    RoomOccupancy,
    Money,
    RoomRate,
    HotelReviews,
)
from api.locations.location_service import find_city_by_simplenight_id
from api.models.models import ProviderImages, ProviderHotel
from api.view.exceptions import AvailabilityException, BookingException, AvailabilityErrorCode, BookingErrorCode


class HotelbedsAdapter(HotelAdapter):
    def __init__(self, transport=None):
        self.transport = transport
        if self.transport is None:
            self.transport = HotelbedsTransport(test_mode=True)

        self.adapter_info = HotelbedsInfo()
        self.provider = self.adapter_info.get_or_create_provider_id()

    def search_by_location(self, search: AdapterLocationSearch) -> List[AdapterHotel]:
        request = self._create_location_search(search)

        response = self.transport.hotels(**request)
        hotel_results = self._check_hotels_response_and_get_results(response)
        if len(hotel_results) == 0:
            return

        hotels = self._create_hotels_from_response(search, hotel_results)

        return hotels

    def search_by_id(self, search: AdapterHotelSearch) -> AdapterHotel:
        request = self._create_hotel_id_search(search)

        response = self.transport.hotels(**request)
        hotel_results = self._check_hotels_response_and_get_results(response)
        if len(hotel_results) == 0:
            return

        hotels = self._create_hotels_from_response(search, hotel_results)

        return hotels[0]

    def search_by_id_batch(self, search: AdapterHotelBatchSearch) -> List[AdapterHotel]:
        request = self._create_hotel_id_batch_search(search)

        response = self.transport.hotels(**request)
        hotel_results = self._check_hotels_response_and_get_results(response)
        if len(hotel_results) == 0:
            return

        hotels = self._create_hotels_from_response(search, hotel_results)

        return hotels

    def _create_location_search(self, search: AdapterLocationSearch):
        """
        convert location search to geolocation
        """
        location = find_city_by_simplenight_id(
            search.location_id, language_code=(search.language if search.language else "en")
        )
        if location is None:
            raise AvailabilityException(
                error_type=AvailabilityErrorCode.LOCATION_NOT_FOUND, detail="Could not find provider location mapping"
            )

        return {
            **self._create_base_search(search),
            "geolocation": {
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "radius": 30,
                "unit": "mi",
            },
        }

    def _create_hotel_id_search(self, search: AdapterHotelSearch):
        return {**self._create_base_search(search), "hotels": {"hotel": [search.provider_hotel_id]}}

    def _create_hotel_id_batch_search(self, search: AdapterHotelBatchSearch):
        return {**self._create_base_search(search), "hotels": {"hotel": search.provider_hotel_ids}}

    @staticmethod
    def _create_base_search(search: AdapterBaseSearch):
        params = {
            "stay": {
                "checkIn": search.start_date.strftime("%Y-%m-%d"),
                "checkOut": search.end_date.strftime("%Y-%m-%d"),
            },
            "language": get_language_mapping(search.language),
            "occupancies": [
                {
                    "adults": search.occupancy.adults,
                    "children": search.occupancy.children,
                    "rooms": search.occupancy.num_rooms,
                }
            ],
        }

        return params

    def _create_hotels_from_response(self, search, hotels_response):
        hotel_codes = list(x["code"] for x in hotels_response)
        logger.info(f"Enrichment: Looking up {len(hotel_codes)} hotels")
        hotelbeds_hotels = ProviderHotel.objects.filter(
            provider__name=self.get_provider_name(),
            provider_code__in=hotel_codes,
            language_code=(search.language if search.language else "en"),
        )
        hotel_details_map = {x.provider_code: x for x in hotelbeds_hotels}
        logger.info(f"Enrichment: Found {len(hotel_details_map)} stored hotels")

        logger.info(f"Enrichment: Looking up images for {len(hotel_codes)} hotels")
        hotel_images = ProviderImages.objects.filter(provider=self.provider, provider_code__in=hotel_codes)
        logger.info(f"Enrichment: Found {len(hotel_images)} stored images")

        hotel_images_by_id = defaultdict(list)
        for image in hotel_images:
            hotel_images_by_id[str(image.provider_code)].append(image)

        result = []
        for hotel in hotels_response:
            hotel_code = str(hotel["code"])
            if hotel_code not in hotel_details_map:
                continue

            hotel_detail_model = hotel_details_map[hotel_code]
            photos = hotel_images_by_id.get(hotel_code) or []
            if not photos or len(photos) == 0:
                continue
            hotel_details = self._create_hotel_details(hotel, hotel_detail_model, photos)

            room_types = self._create_room_types(hotel, photos)
            rate_plans = self._create_rate_plans(hotel)
            room_rates = self._create_room_rates(hotel)

            result.append(
                AdapterHotel(
                    provider=HotelbedsInfo.name,
                    hotel_id=hotel_code,
                    start_date=search.start_date,
                    end_date=search.end_date,
                    occupancy=search.occupancy,
                    room_types=room_types,
                    rate_plans=rate_plans,
                    room_rates=room_rates,
                    hotel_details=hotel_details,
                )
            )

        return result

    def details(self, *args) -> HotelDetails:
        pass

    def reviews(self, *args) -> HotelReviews:
        raise NotImplementedError()

    def recheck(self, room_rate: RoomRate) -> RoomRate:
        request = self._create_recheck_params(room_rate)

        response = self.transport.checkrates(**request)
        hotel_result = self._check_checkrates_response_and_get_results(response)

        room_type_code = hotel_result["rooms"][0]["code"]
        room_rate = hotel_result["rooms"][0]["rates"][0]

        return self._create_room_rate(room_type_code, room_rate, hotel_result["currency"])

    def book(self, book_request: AdapterHotelBookingRequest) -> HotelReservation:
        request = self._create_booking_params(book_request)
        response = self.transport.booking(**request)

        results = self._check_booking_response_and_get_results(response)
        booking_locator = results["reference"]
        hotel_data = results["hotel"]

        checkin = datetime.strptime(hotel_data["checkIn"], "%Y-%m-%d").date()
        checkout = datetime.strptime(hotel_data["checkOut"], "%Y-%m-%d").date()

        booked_rate_data = hotel_data["rooms"][0]["rates"][0]
        booked_room_rate = self._create_room_rates(hotel_data)[0]

        cancellation_details = self._parse_cancellation_details(booked_rate_data, hotel_data["currency"])

        return HotelReservation(
            locator=Locator(id=booking_locator),
            hotel_locator=None,
            hotel_id=book_request.hotel_id,
            checkin=checkin,
            checkout=checkout,
            customer=book_request.customer,
            traveler=book_request.traveler,
            room_rate=booked_room_rate,
            cancellation_details=cancellation_details,
        )

    def cancel(self, cancel_request: AdapterCancelRequest) -> AdapterCancelResponse:
        lookup_request = {"language": cancel_request.language}
        lookup_response = self.transport.booking_detail(cancel_request.record_locator, **lookup_request)
        lookup_result = self._check_booking_response_and_get_results(lookup_response)

        if (
            "cancellation" not in lookup_result["modificationPolicies"]
            or not lookup_result["modificationPolicies"]["cancellation"]
        ):
            raise BookingException(BookingErrorCode.PROVIDER_CANCELLATION_FAILURE, "Could not cancel booking")

        request = {"cancellationFlag": "CANCELLATION", "language": cancel_request.language}
        cancel_response = self.transport.booking_cancel(cancel_request.record_locator, **request)
        cancel_result = self._check_booking_response_and_get_results(cancel_response)

        if cancel_result["status"] != "CANCELLED":
            logger.error(f"Could not cancel booking {cancel_request}: {cancel_response}")
            raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Could not cancel booking")

        return AdapterCancelResponse(is_cancelled=True)

    @classmethod
    def factory(cls, test_mode=True):
        return HotelbedsAdapter(HotelbedsTransport(test_mode=test_mode))

    @classmethod
    def get_provider_name(cls):
        return HotelbedsInfo.name

    @staticmethod
    def _create_room_types(hotel_response, photos):
        room_types = []
        for room in hotel_response["rooms"]:
            adults = max(x.get("adults", 0) for x in room["rates"])
            children = max(x.get("children", 0) for x in room["rates"])
            occupancy = RoomOccupancy(adults=adults, children=children)
            room_photos = list(filter(lambda image: room["code"] == json.loads(
                image.meta_info).get("room_code", None), photos))

            room_type = RoomType(
                code=room["code"],
                name=room["name"],
                description=room["name"],
                amenities=[],
                photos=list(map(HotelbedsAdapter._get_image, room_photos)),
                capacity=occupancy,
                bed_types=None,
            )

            room_types.append(room_type)

        return room_types

    def _create_rate_plans(self, hotel_response):
        rate_plans = []
        for room in hotel_response["rooms"]:
            for rate in room["rates"]:
                cancellation_details = self._parse_cancellation_details(rate, hotel_response["currency"])
                most_lenient_cancellation_policy = self._cancellation_summary_from_details(cancellation_details)
                rate_plan = RatePlan(
                    code=rate["rateKey"],
                    name="",
                    description="",
                    amenities=[],
                    cancellation_policy=most_lenient_cancellation_policy,
                )
                rate_plans.append(rate_plan)

        return rate_plans

    @staticmethod
    def _parse_cancellation_details(rate, currency) -> List[CancellationDetails]:
        total_rate = rate["net"]
        cancellation_detail_list = []
        if "cancellationPolicies" not in rate or len(rate["cancellationPolicies"]) == 0:
            return [
                CancellationDetails(
                    cancellation_type=CancellationSummary.UNKNOWN_CANCELLATION_POLICY,
                    description="Cancellation policy unspecified",
                    begin_date=datetime.now() - relativedelta(years=1),
                    end_date=datetime.now() + relativedelta(years=5),
                    penalty_amount=total_rate,
                    penalty_currency=currency,
                )
            ]

        for cancellation_detail_response in rate["cancellationPolicies"]:
            total_penalty = cancellation_detail_response["amount"]
            from_date = datetime.fromisoformat(cancellation_detail_response["from"])
            # end_date=datetime.now() + relativedelta(years=5)

            cancellation_type = CancellationSummary.NON_REFUNDABLE
            current_time = datetime.now(tz=pytz.timezone("US/Pacific"))
            penalty_currency = cancellation_detail_response.get("hotelCurrency", currency)

            if current_time <= from_date:
                if Decimal(total_penalty) == Decimal(rate["net"]):
                    cancellation_type = CancellationSummary.FREE_CANCELLATION
                elif Decimal(total_penalty) < Decimal(rate["net"]):
                    cancellation_type = CancellationSummary.PARTIAL_REFUND

            cancellation_detail = CancellationDetails(
                cancellation_type=cancellation_type,
                description="",
                begin_date=from_date,
                end_date=None,
                penalty_amount=total_penalty,
                penalty_currency=penalty_currency,
            )

            cancellation_detail_list.append(cancellation_detail)

        return cancellation_detail_list

    @staticmethod
    def _cancellation_summary_from_details(cancellation_details: List[CancellationDetails],) -> CancellationPolicy:
        sort_order = {
            CancellationSummary.FREE_CANCELLATION: 0,
            CancellationSummary.PARTIAL_REFUND: 1,
            CancellationSummary.NON_REFUNDABLE: 2,
        }

        most_lenient_policy = sorted(cancellation_details, key=lambda x: sort_order.get(x.cancellation_type))[0]

        return CancellationPolicy(
            summary=most_lenient_policy.cancellation_type,
            cancellation_deadline=most_lenient_policy.end_date,
            unstructured_policy=most_lenient_policy.description,
        )

    def _create_room_rates(self, hotel_response):
        room_rates = []
        for room in hotel_response["rooms"]:
            for rate in room["rates"]:
                room_rates.append(self._create_room_rate(room["code"], rate, hotel_response["currency"]))

        return room_rates

    @staticmethod
    def _create_room_rate(room_type_code: str, rate: Dict[Any, Any], currency="USD"):
        net_amount = Decimal(rate.get("net", 0))

        total_base_rate = Money(amount=net_amount, currency=currency)
        total_taxes = 0
        if "taxes" in rate:
            total_taxes = sum(Decimal(x["amount"]) for x in rate["taxes"]["taxes"] if "amount" in x)

        total_tax_rate = Money(amount=total_taxes, currency=currency)
        total_amount = total_base_rate.amount + total_tax_rate.amount
        total_rate = Money(amount=total_amount, currency=currency)

        occupancy = RoomOccupancy(
            adults=rate.get("adults", 0), children=rate.get("children", 0), num_rooms=rate.get("rooms", 0)
        )

        rate_type = rate.get("rateType", "BOOKABLE")
        rate_plan_code = rate.get("rateKey", "")

        return RoomRate(
            code=rate_plan_code,
            rate_plan_code=rate_plan_code,
            room_type_code=room_type_code,
            rate_type=rate_type,
            total_base_rate=total_base_rate,
            total_tax_rate=total_tax_rate,
            total=total_rate,
            maximum_allowed_occupancy=occupancy,
        )

    def _check_hotels_response_and_get_results(self, response):
        results = self._check_operation_response_and_get_results(response, "hotels")
        hotels = results.get("hotels", [])
        if len(hotels) == 0:
            raise AvailabilityException(
                error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail="Could not retrieve response",
            )
        return hotels

    def _check_checkrates_response_and_get_results(self, response):
        results = self._check_operation_response_and_get_results(response, "hotel")
        return results

    @staticmethod
    def _check_operation_response_and_get_results(response, operation):
        if response is None:
            raise AvailabilityException(
                error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail="Could not retrieve response",
            )
        if "error" in response:
            error_message = response["error"]
            if "message" in error_message:
                error_message = error_message["message"]
            logger.error("Error in Hotelbeds Message: " + error_message)
            raise AvailabilityException(error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail=error_message)

        return response[operation]

    @staticmethod
    def _create_booking_params(book_request: AdapterHotelBookingRequest):
        customer = book_request.customer

        return {
            "holder": {"name": customer.first_name, "surname": customer.last_name},
            "clientReference": book_request.transaction_id.replace("-", "")[:20],
            "rooms": [
                {
                    "rateKey": book_request.room_code,
                    "paxes": [
                        {
                            "roomId": 1,
                            "type": "AD",
                            "name": book_request.traveler.first_name,
                            "surname": book_request.traveler.last_name,
                        }
                    ],
                }
            ],
            "tolerance": 2,
            "remark": book_request.additional_info or "",
        }

    @staticmethod
    def _check_booking_response_and_get_results(response):
        if response is None:
            raise BookingException(
                error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail="Could not retrieve response",
            )
        if "error" in response:
            error_message = response["error"]
            if "message" in error_message:
                error_message = error_message["message"]
            logger.error("Error in Hotelbeds Message: " + error_message)
            raise BookingException(error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail=error_message)

        return response["booking"]

    @staticmethod
    def _get_image(provider_image: ProviderImages):
        return Image(
            url=provider_image.image_url,
            type=get_image_type(provider_image.type),
            display_order=provider_image.display_order,
        )

    @staticmethod
    def _create_hotel_details(hotel, hotel_detail_model: ProviderHotel, photos):
        star_rating = None
        if hotel_detail_model.star_rating:
            star_rating = float(hotel_detail_model.star_rating)

        return HotelDetails(
            name=hotel["name"],
            address=hotel_detail_model.get_address(),
            hotel_code=str(hotel["code"]),
            checkin_time=None,
            checkout_time=None,
            photos=list(map(HotelbedsAdapter._get_image, photos)),
            thumbnail_url=hotel_detail_model.thumbnail_url,
            amenities=get_simplenight_amenity_mappings(hotel_detail_model.amenities),
            geolocation=GeoLocation(latitude=hotel["latitude"], longitude=hotel["longitude"]),
            chain_code=hotel_detail_model.chain_code,
            chain_name=hotel_detail_model.chain_name,
            star_rating=star_rating,
            property_description=hotel_detail_model.property_description,
        )

    @staticmethod
    def _create_recheck_params(room_rate: RoomRate):
        return {"rooms": [{"rateKey": room_rate.code}]}
