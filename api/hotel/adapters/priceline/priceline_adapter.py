import distutils.util
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Any, Dict, Union

import pytz
from dateutil.relativedelta import relativedelta

from api import logger
from api.hotel.adapters import adapter_common
from api.hotel.adapters.hotel_adapter import HotelAdapter
from api.hotel.adapters.priceline import priceline_amenity_mappings
from api.hotel.adapters.priceline.priceline_info import PricelineInfo
from api.hotel.adapters.priceline.priceline_transport import PricelineTransport
from api.hotel.models.adapter_models import (
    AdapterLocationSearch,
    AdapterBaseSearch,
    AdapterHotelSearch,
    AdapterCancelRequest,
    AdapterCancelResponse,
    AdapterHotelBatchSearch,
)
from api.hotel.models.booking_model import (
    Customer,
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
    GeoLocation,
    SimplenightAmenities,
    Image,
    ImageType,
    CancellationDetails,
)
from api.hotel.models.hotel_common_models import (
    RoomOccupancy,
    Address,
    RateType,
    Money,
    LineItemType,
    PostpaidFeeLineItem,
    PostpaidFees,
    RoomRate,
    HotelReviews,
    HotelReview,
)
from api.models.models import ProviderImages, ProviderHotel
from api.view.exceptions import (
    AvailabilityException,
    BookingException,
    AvailabilityErrorCode,
    BookingErrorCode,
)


class PricelineAdapter(HotelAdapter):
    def __init__(self, transport=None):
        self.transport = transport
        if self.transport is None:
            self.transport = PricelineTransport(test_mode=True)

        self.adapter_info = PricelineInfo()
        self.provider = self.adapter_info.get_or_create_provider_id()

    def search_by_location(self, search: AdapterLocationSearch) -> List[AdapterHotel]:
        request = self._create_city_search(search)
        logger.info(f"Initiating Priceline City Express Search: {request}")

        response = self.transport.hotel_express(limit=250, **request)
        hotel_results = self._check_hotel_express_response_and_get_results(response)

        hotels = list(map(lambda result: self._create_hotel_from_response(search, result), hotel_results,))
        self._enrich_hotels(hotels)

        return hotels

    def search_by_id(self, search: AdapterHotelSearch) -> AdapterHotel:
        request = self._create_hotel_id_search(search)
        logger.info(f"Initiating Priceline Hotel Express Search: {request}")

        response = self.transport.hotel_express(**request)

        hotel_results = self._check_hotel_express_response_and_get_results(response)
        hotel = self._create_hotel_from_response(search, hotel_results[0])

        self._enrich_hotels(hotel)
        self._apply_room_details(hotel)

        return hotel

    # TODO (JLM): Combine with search_by_id
    def search_by_id_batch(self, search: AdapterHotelBatchSearch) -> List[AdapterHotel]:
        request = self._create_hotel_id_batch_search(search)
        logger.info(f"Initiating Priceline Hotel Express batch Search: {request}")

        response = self.transport.hotel_express(**request)
        hotel_results = self._check_hotel_express_response_and_get_results(response)
        hotels = list(self._create_hotel_from_response(search, x) for x in hotel_results)

        self._enrich_hotels(hotels)

        return hotels

    def details(self, *args) -> HotelDetails:
        pass

    def reviews(self, hotel_id) -> HotelReviews:
        def parse_review_data(data):
            return HotelReview(
                reviewer_name=data["user_name"],
                review_date=data["creation_date"],
                review_rating=data["average_rating"],
                review_text=data["review_text"],
                good_text=data["good_description"],
                bad_text=data["bad_description"],
            )

        response = self.transport.hotel_reviews(hotel_id=hotel_id)
        results = self._check_reviews_response_and_get_results(response)

        if not results["review_data"]:
            return HotelReviews(average_rating=0.0, review_count=0, reviews=[])

        return HotelReviews(
            average_rating=results["review_rating"],
            review_count=results["review_count"],
            reviews=list(map(parse_review_data, results["review_data"])),
        )

    def cancel(self, cancel_request: AdapterCancelRequest) -> AdapterCancelResponse:
        # Priceline first requires a lookup call, to retrieve a "Cancel action"
        # Per Justin Steele, we have hard-coded "info@simplenight.com" as the email associated with bookings
        lookup_response = self.transport.express_lookup(
            booking_id=cancel_request.record_locator, email="info@simplenight.com",
        )
        lookup_response = self._check_express_lookup_response_and_get_results(lookup_response)

        if "cancel" not in lookup_response["result"]["actions"]:
            raise BookingException(BookingErrorCode.PROVIDER_CANCELLATION_FAILURE, "Could not cancel booking")

        cancellation_code = lookup_response["result"]["actions"]["cancel"]
        logger.info(f"Successfully looked up booking {cancel_request.record_locator}")

        cancel_response = self.transport.express_cancel(ppn_bundle=cancellation_code)
        cancel_response = self._check_express_cancel_response_and_get_results(cancel_response)

        if cancel_response["result"]["status"] != "Cancelled":
            logger.error(f"Could not cancel booking {cancel_request}: {cancel_response}")
            raise BookingException(BookingErrorCode.CANCELLATION_FAILURE, "Could not cancel booking")

        return AdapterCancelResponse(is_cancelled=True)

    def room_details(self, ppn_bundle: str) -> Dict:
        logger.info("Retrieving room details for PPN bundle: " + ppn_bundle)
        params = {"ppn_bundle": ppn_bundle}
        response = self.transport.express_contract(**params)

        hotel_data = self._check_hotel_express_contract_response_and_get_results(response)[0]
        rate_plans = self._create_rate_plans(hotel_data)
        postpaid_fees = self._get_postpaid_fees_from_contract_response(response)

        return {
            "hotel_data": hotel_data,
            "rate_plans": rate_plans,
            "postpaid_fees": postpaid_fees,
            "room_date": hotel_data["room_data"][0],
            "rate_data": hotel_data["room_data"][0]["rate_data"][0],
            "room_id": hotel_data["room_data"][0]["id"],
        }

    def book(self, book_request: AdapterHotelBookingRequest) -> HotelReservation:
        params = self._create_booking_params(book_request.customer, book_request.room_code)
        response = self.transport.express_book(**params)

        results = self._check_express_book_response_and_get_results(response)

        booking_data = results["book_data"]
        contract_data = results["contract_data"]
        booking_locator = booking_data["itinerary"]["id"]
        room_data = booking_data["itinerary_details"]["room_data"]
        hotel_locators = [Locator(id=room["confirmation_code"]) for room in room_data]

        checkin = date.fromisoformat(booking_data["itinerary"]["check_in"])
        checkout = date.fromisoformat(booking_data["itinerary"]["check_out"])

        contract_room_data = contract_data["hotel_data"][0]["room_data"][0]
        contract_room_id = contract_room_data["id"]
        booked_rate_data = contract_room_data["rate_data"][0]
        booked_rate_plan = self._create_rate_plans(contract_data["hotel_data"][0])[0]
        booked_room_rate = self._create_room_rate(contract_room_id, booked_rate_data, booked_rate_plan)

        cancellation_details = self._parse_cancellation_details(booked_rate_data)

        return HotelReservation(
            locator=Locator(id=booking_locator),
            hotel_locator=hotel_locators,
            hotel_id=book_request.hotel_id,
            checkin=checkin,
            checkout=checkout,
            customer=book_request.customer,
            traveler=book_request.traveler,
            room_rate=booked_room_rate,
            cancellation_details=cancellation_details,
        )

    def _get_postpaid_fees_from_contract_response(self, contract_response):
        results = contract_response["getHotelExpress.Contract"]["results"]
        if results["status"] != "Success":
            raise AvailabilityException(
                detail="Could not parse postpaid fees", error_type=AvailabilityErrorCode.PROVIDER_ERROR,
            )

        room_data = results["hotel_data"][0]["room_data"][0]
        rate_data = room_data["rate_data"][0]

        return self._parse_postpaid_fees_from_priceline_rate(rate_data)

    def _parse_postpaid_fees_from_priceline_rate(self, rate_data):
        mandatory_fees = rate_data["price_details"]["mandatory_fee_details"]

        if not mandatory_fees:
            return None

        postpaid_fee_breakdown = mandatory_fees["breakdown"]["postpaid"]
        postpaid_total_currency = postpaid_fee_breakdown["display_currency"]
        postpaid_total_fee = Decimal(postpaid_fee_breakdown["display_total"])
        postpaid_total = Money(amount=round(postpaid_total_fee, 2), currency=postpaid_total_currency)

        postpaid_fees = []
        for postpaid_fee in postpaid_fee_breakdown["breakdown"]:
            fee_amount = round(Decimal(postpaid_fee["display_total"]), 2)
            fee_currency = postpaid_fee["display_currency"]
            priceline_fee_type = postpaid_fee["type"]

            fee = Money(amount=fee_amount, currency=fee_currency)
            fee_type = self._parse_postpaid_fee_type(priceline_fee_type)

            postpaid_fees.append(PostpaidFeeLineItem(amount=fee, type=fee_type, description=priceline_fee_type))

        return PostpaidFees(total=postpaid_total, fees=postpaid_fees)

    @staticmethod
    def _parse_postpaid_fee_type(fee_type):
        default = LineItemType.UNKNOWN_FEES
        return {}.get(fee_type, default)

    def _apply_room_details(self, hotel: AdapterHotel):
        """Disabled, because postpaid fees are in initial hotel results"""

    def _room_details_map(self, hotel: AdapterHotel) -> Dict[str, Dict]:
        room_codes = [rate.code for rate in hotel.room_rates]
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(lambda room_code: (room_code, self.room_details(room_code)), room_codes)

        return {room_code: room_details for room_code, room_details in results}

    def recheck(self, room_rate: RoomRate) -> RoomRate:
        room_details = self.room_details(room_rate.code)
        room_id = room_details["room_id"]
        rate_data = room_details["rate_data"]
        rate_plan = room_details["rate_plans"][0]

        return self._create_room_rate(room_id, rate_data, rate_plan)

    def _create_booking_params(self, customer: Customer, rate_code: str):
        payment = adapter_common.get_virtual_credit_card(self.transport.test_mode)
        payment_card_params = payment.payment_card_parameters
        expires_string = f"{int(payment_card_params.expiration_month):02d}{payment_card_params.expiration_year}"
        return {
            "ppn_bundle": rate_code,
            "name_first": customer.first_name,
            "name_last": customer.last_name,
            "phone_number": customer.phone_number,
            "email": "info@simplenight.com",  # Per Justin Steele, use Simplenight Email Address in All Cases
            "card_holder": payment_card_params.cardholder_name,
            "address_line_one": payment.billing_address.address1,
            "address_city": payment.billing_address.city,
            "address_state_code": payment.billing_address.province,
            "country_code": payment.billing_address.country,
            "address_postal_code": payment.billing_address.postal_code,
            "card_type": payment_card_params.card_type.name,
            "card_number": payment_card_params.card_number,
            "expires": expires_string,
            "cvc_code": payment_card_params.cvv,
        }

    def _create_hotel_id_search(self, search: AdapterHotelSearch):
        return {
            **self._create_base_search(search),
            "hotel_ids": search.provider_hotel_id,
        }

    def _create_hotel_id_batch_search(self, search: AdapterHotelBatchSearch):
        hotel_search = self._create_base_search(search)
        hotel_search["hotel_ids"] = str.join(",", search.provider_hotel_ids)

        return hotel_search

    def _create_city_search(self, search: AdapterLocationSearch):
        priceline_location = self.get_provider_location(search)
        priceline_location_code = priceline_location.provider_code

        logger.info(f"Resolved Simplenight Location ID {search.location_id} to {priceline_location_code}")
        return {
            **self._create_base_search(search),
            "city_id": priceline_location_code,
        }

    def _enrich_hotels(self, hotels: Union[List[AdapterHotel], AdapterHotel]):
        logger.info("Enrichment: Begin")
        if isinstance(hotels, AdapterHotel):
            hotels = [hotels]

        hotel_codes = list(x.hotel_id for x in hotels)
        logger.info(f"Enrichment: Looking up {len(hotel_codes)} hotels")
        priceline_hotels = ProviderHotel.objects.filter(
            provider__name=self.get_provider_name(), provider_code__in=hotel_codes
        )
        hotel_details_map = {x.provider_code: x for x in priceline_hotels}
        logger.info(f"Enrichment: Found {len(hotel_details_map)} stored hotels")

        logger.info(f"Enrichment: Looking up images for {len(hotel_codes)} hotels")
        hotel_images = ProviderImages.objects.filter(provider=self.provider, provider_code__in=hotel_codes)
        logger.info(f"Enrichment: Found {len(hotel_images)} stored images")

        hotel_images_by_id = defaultdict(list)
        for image in hotel_images:
            hotel_images_by_id[image.provider_code].append(image)

        for hotel in hotels:
            if hotel.hotel_id not in hotel_details_map:
                continue

            hotel_detail_model = hotel_details_map[hotel.hotel_id]
            hotel.hotel_details.photos = list(map(self._get_image, hotel_images_by_id.get(hotel.hotel_id) or []))
            hotel.hotel_details.thumbnail_url = hotel_detail_model.thumbnail_url
            hotel.hotel_details.amenities = priceline_amenity_mappings.get_simplenight_amenity_mappings(
                hotel_detail_model.amenities
            )

        logger.info("Enrichment: Complete")

    @staticmethod
    def _get_image(provider_image: ProviderImages):
        return Image(url=provider_image.image_url, type=ImageType.UNKNOWN, display_order=provider_image.display_order,)

    @staticmethod
    def _get_amenity_mappings(amenities: List[str]):
        return list(map(SimplenightAmenities.from_value, amenities))

    @staticmethod
    def _create_base_search(search: AdapterBaseSearch):
        params = {
            "check_in": search.start_date,
            "check_out": search.end_date,
            "adults": search.occupancy.adults,
            "children": search.occupancy.children,
            "rooms": search.occupancy.num_rooms,
        }

        if search.currency:
            params["currency"] = search.currency

        return params

    @staticmethod
    def _check_hotel_express_operation_response_and_get_results(response, operation):
        if response is None or operation not in response:
            raise AvailabilityException(
                error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail="Could not retrieve response",
            )

        results = response[operation]
        if "error" in results:
            error_message = results["error"]["status"]
            logger.error("Error in Priceline Message: " + error_message)
            raise AvailabilityException(error_type=AvailabilityErrorCode.PROVIDER_ERROR, detail=error_message)

        return results["results"]

    def _check_hotel_express_response_and_get_results(self, response):
        results = self._check_hotel_express_operation_response_and_get_results(response, "getHotelExpress.Results")
        return results["hotel_data"]

    def _check_hotel_express_contract_response_and_get_results(self, response):
        results = self._check_hotel_express_operation_response_and_get_results(response, "getHotelExpress.Contract")
        return results["hotel_data"]

    def _check_express_lookup_response_and_get_results(self, response):
        return self._check_hotel_express_operation_response_and_get_results(response, "getHotelExpress.LookUp")

    def _check_express_cancel_response_and_get_results(self, response):
        return self._check_hotel_express_operation_response_and_get_results(response, "getHotelExpress.Cancel")

    def _check_reviews_response_and_get_results(self, response):
        return self._check_hotel_express_operation_response_and_get_results(response, "getHotelReviews")

    @staticmethod
    def _check_express_book_response_and_get_results(response):
        error_type = AvailabilityErrorCode.PROVIDER_ERROR
        if response is None or "getHotelExpress.Book" not in response:
            raise BookingException(error_type=error_type, detail="Could not retrieve response")

        results = response["getHotelExpress.Book"]
        if "error" in results:
            error_message = results["error"]["status"]
            raise BookingException(error_type=error_type, detail=error_message)

        return results["results"]

    def _create_hotel_from_response(self, search, hotel_response):
        room_types = self._create_room_types(hotel_response)
        rate_plans = self._create_rate_plans(hotel_response)
        room_rates = self._create_room_rates(hotel_response, rate_plans)
        hotel_details = self._create_hotel_details(hotel_response)

        return AdapterHotel(
            provider=PricelineInfo.name,
            hotel_id=hotel_response["id"],
            start_date=search.start_date,
            end_date=search.end_date,
            occupancy=search.occupancy,
            room_types=room_types,
            rate_plans=rate_plans,
            room_rates=room_rates,
            hotel_details=hotel_details,
        )

    @staticmethod
    def _create_hotel_details(hotel_data):
        address_response = hotel_data["address"]
        address = Address(
            city=address_response["city_name"],
            province=address_response["state_code"],
            country=address_response["country_code"],
            address1=address_response["address_line_one"],
            postal_code=address_response["zip"],
        )

        return HotelDetails(
            name=hotel_data["name"],
            address=address,
            hotel_code=hotel_data["id"],
            checkin_time=None,
            checkout_time=None,
            photos=[],
            amenities=[],
            geolocation=GeoLocation(latitude=hotel_data["geo"]["latitude"], longitude=hotel_data["geo"]["longitude"],),
            chain_code=hotel_data["hotel_chain"]["chain_codes_t"],
            chain_name=hotel_data["hotel_chain"]["name"],
            star_rating=hotel_data["star_rating"],
            review_rating=hotel_data["review_rating"],
            property_description=hotel_data["hotel_description"],
        )

    def _create_room_rate(self, room_id: str, rate_data: Dict[Any, Any], rate_plan) -> RoomRate:
        rate_code = PricelineAdapter.get_ppn_bundle_code(rate_data)
        price_details = rate_data["price_details"]
        display_currency = price_details["display_currency"]

        return RoomRate(
            code=rate_code,
            room_type_code=room_id,
            rate_plan_code=rate_plan.code,
            maximum_allowed_occupancy=self._get_room_capacity(rate_data),
            total_base_rate=Money(amount=Decimal(price_details["display_sub_total"]), currency=display_currency,),
            total_tax_rate=Money(amount=Decimal(price_details["display_taxes"]), currency=display_currency,),
            total=Money(amount=Decimal(price_details["display_total"]), currency=display_currency,),
            rate_type=RateType.BOOKABLE,
            postpaid_fees=self._parse_postpaid_fees_from_priceline_rate(rate_data),
        )

    @staticmethod
    def _get_room_capacity(rate_data: Dict[Any, Any]) -> RoomOccupancy:
        adults = rate_data["occupancy_limit"]
        if not adults:
            adults = 2

        return RoomOccupancy(adults=adults)

    @staticmethod
    def get_ppn_bundle_code(rate_data):
        if "ppn_book_bundle" in rate_data:
            return rate_data["ppn_book_bundle"]
        else:
            return rate_data["ppn_bundle"]

    def _create_room_rates(self, hotel_response, rate_plans):
        room_rates = []
        for room in hotel_response["room_data"]:
            for rate in room["rate_data"]:
                room_id = room["id"]
                room_rates.append(self._create_room_rate(room_id, rate, rate_plans[0]))

        return room_rates

    def _create_rate_plans(self, hotel_response):
        """
        Currently, we only support cancellable/non-cancellable rate plans.
        Priceline rooms are all non-cancellable.  So we return one rate plan.
        """

        rate_plans = []
        for room in hotel_response["room_data"]:
            for rate in room["rate_data"]:
                cancellation_details = self._parse_cancellation_details(rate)
                most_lenient_cancellation_policy = self._cancellation_summary_from_details(cancellation_details)

                rate_plan = RatePlan(
                    code=rate["rate_plan_code"],
                    name=rate["title"],
                    description=rate["description"],
                    amenities=[],
                    cancellation_policy=most_lenient_cancellation_policy,
                )
                rate_plans.append(rate_plan)

        return rate_plans

    @staticmethod
    def _parse_cancellation_details(rate) -> List[CancellationDetails]:
        """Parses Detailed Cancellation Data.  This is used when storing a booking,
        but only a summary of this data is returned on availability
        """

        total_rate = rate["price_details"]["display_total"]
        is_cancellable = distutils.util.strtobool(rate["is_cancellable"])
        if not is_cancellable:
            logger.debug(f"Found non-refundable rate for rate plan {rate['rate_plan_code']}")
            return [
                CancellationDetails(
                    cancellation_type=CancellationSummary.NON_REFUNDABLE,
                    description="Non refundable room rate",
                    begin_date=datetime.now() - relativedelta(years=1),
                    end_date=datetime.now() + relativedelta(years=5),
                    penalty_amount=total_rate,
                    penalty_currency=rate["price_details"]["display_currency"],
                )
            ]

        cancellation_detail_lst = []
        priceline_cancellation_details = rate["cancellation_details"]
        if not priceline_cancellation_details:
            unknown_cancellation_policy = CancellationDetails(
                cancellation_type=CancellationSummary.UNKNOWN_CANCELLATION_POLICY,
                description="Cancellation policy unspecified",
                begin_date=datetime.now() - relativedelta(years=1),
                end_date=datetime.now() + relativedelta(years=5),
                penalty_amount=total_rate,
                penalty_currency=rate["price_details"]["display_currency"],
            )

            return [unknown_cancellation_policy]

        for cancellation_detail_response in rate["cancellation_details"]:
            total_penalty = cancellation_detail_response["display_total_charges"]
            penalty_currency = cancellation_detail_response["display_currency"]
            description = cancellation_detail_response["description"]
            begin_date = datetime.fromisoformat(cancellation_detail_response["date_after"])
            end_date = datetime.fromisoformat(cancellation_detail_response["date_before"])

            cancellation_type = CancellationSummary.NON_REFUNDABLE
            current_time = datetime.now(tz=pytz.timezone("US/Pacific"))

            if total_penalty == 0 and current_time < end_date:
                cancellation_type = CancellationSummary.FREE_CANCELLATION
            elif total_penalty < total_rate and current_time < end_date:
                cancellation_type = CancellationSummary.PARTIAL_REFUND

            cancellation_detail = CancellationDetails(
                cancellation_type=cancellation_type,
                description=description,
                begin_date=begin_date,
                end_date=end_date,
                penalty_amount=total_penalty,
                penalty_currency=penalty_currency,
            )

            cancellation_detail_lst.append(cancellation_detail)

        return cancellation_detail_lst

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

    def _create_room_types(self, hotel_response):
        """
        RoomTypes and Rate Plans, and Rates are returned together by Priceline.
        Priceline supports an alternative format, where room types are grouped together.
        See Here: https://developer.pricelinepartnernetwork.com/guides/id/room-id-grouping
        This is the format that the Simplenight front-end requires.  That is, each room type is returned
        with a price, the services/cancellation policies in supports, and rates, all together.
        However, this is not the format requested by Google, and not the format returned by other connectors.
        So we parse out room type details from the rate data.
        """

        # TODO: See if we have room photos in downloadable content
        room_types = []
        for room in hotel_response["room_data"]:
            rate_data = room["rate_data"][0]
            room_type = RoomType(
                code=room["id"],
                name=rate_data["title"],
                description=rate_data["description"],
                amenities=[],
                photos=[],
                capacity=self._get_room_capacity(rate_data),
                bed_types=None,
            )

            room_types.append(room_type)
        return room_types

    @classmethod
    def factory(cls, test_mode=True):
        return PricelineAdapter(PricelineTransport(test_mode=test_mode))

    @classmethod
    def get_provider_name(cls):
        return PricelineInfo.name


class PricelineErrorCodes(Enum):
    GENERIC_ERROR = 1
    AVAILABILITY_ERROR = 2
    GENERIC_BOOKING_ERROR = 3
    BOOKING_FAILURE = 4
