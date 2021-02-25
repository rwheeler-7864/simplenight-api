from decimal import Decimal
from typing import List

from api.hotel.converter.google_models import (
    GoogleHotelApiResponse,
    GoogleHotelSearchRequest,
    GoogleRoomType,
    DisplayString,
    BasicAmenities,
    GoogleImage,
    RoomCapacity,
    GoogleRatePlan,
    GuaranteeType,
    GoogleCancellationPolicy,
    GoogleRoomRate,
    GoogleHotelDetails,
    GoogleBookingSubmitRequest,
    GoogleTraveler,
    GoogleBookingResponse,
    GoogleStatus,
    GoogleReservation,
    RoomParty,
    RoomRateLineItem,
)
from api.hotel.models.booking_model import (
    HotelBookingRequest,
    Traveler,
    Payment,
    PaymentCardParameters,
    HotelBookingResponse,
    Locator,
)
from api.hotel.models.hotel_api_model import SimplenightAmenities, Image, HotelSpecificSearch, Hotel, CancellationPolicy
from api.hotel.models.hotel_common_models import RoomOccupancy, RateType, Money, RoomRate, LineItemType


def convert_hotel_specific_search(google_search_request: GoogleHotelSearchRequest) -> HotelSpecificSearch:
    return HotelSpecificSearch(
        hotel_id=google_search_request.hotel_id,
        start_date=google_search_request.start_date,
        end_date=google_search_request.end_date,
        occupancy=RoomOccupancy(
            adults=google_search_request.party.adults, children=len(google_search_request.party.children)
        ),
        daily_rates=False,
    )


def convert_booking_request(google_booking_request: GoogleBookingSubmitRequest) -> HotelBookingRequest:
    google_room_rate = google_booking_request.room_rate

    total_price = Decimal()
    if google_room_rate.total_price_at_checkout:
        total_price += google_room_rate.total_price_at_checkout.amount

    if google_room_rate.total_price_at_booking:
        total_price += google_room_rate.total_price_at_booking.amount

    google_room_occupancy = google_booking_request.room_rate.maximum_allowed_occupancy
    room_occupancy = RoomOccupancy(adults=google_room_occupancy.adults, children=google_room_occupancy.children)

    room_rate = RoomRate(
        code=google_booking_request.room_rate.code,
        rate_plan_code=google_booking_request.room_rate.rate_plan_code,
        room_type_code=google_booking_request.room_rate.room_type_code,
        maximum_allowed_occupancy=room_occupancy,
        rate_type=RateType.BOOKABLE,
        total_base_rate=Money(amount=total_price, currency="USD"),
        total_tax_rate=Money(amount=Decimal("0"), currency="USD"),
        total=Money(amount=total_price, currency="USD"),
    )

    google_payment = google_booking_request.payment
    payment = Payment(
        billing_address=google_payment.billing_address,
        payment_card_parameters=PaymentCardParameters(
            card_type=google_payment.payment_card_parameters.card_type,
            card_number=google_payment.payment_card_parameters.card_number,
            cardholder_name=google_payment.payment_card_parameters.cardholder_name,
            expiration_month=google_payment.payment_card_parameters.expiration_month,
            expiration_year=google_payment.payment_card_parameters.expiration_year,
            cvv=google_payment.payment_card_parameters.cvc,
        ),
        payment_method=google_payment.type,
        payment_token=google_payment.payment_token,
    )

    return HotelBookingRequest(
        api_version=google_booking_request.api_version,
        transaction_id=google_booking_request.transaction_id,
        hotel_id=google_booking_request.hotel_id,
        room_code=room_rate.code,
        language=google_booking_request.language,
        customer=google_booking_request.customer,
        traveler=Traveler(
            first_name=google_booking_request.traveler.first_name,
            last_name=google_booking_request.traveler.last_name,
            occupancy=RoomOccupancy(
                adults=google_booking_request.traveler.occupancy.adults,
                children=len(google_booking_request.traveler.occupancy.children),
            ),
        ),
        payment=payment,
    )


def convert_booking_response(
    booking_request: GoogleBookingSubmitRequest, booking_response: HotelBookingResponse
) -> GoogleBookingResponse:
    status = GoogleStatus.FAILURE
    if booking_response.status.success:
        status = GoogleStatus.SUCCESS

    google_booking_response = GoogleBookingResponse(
        api_version=booking_response.api_version,
        transaction_id=booking_response.transaction_id,
        status=status,
        reservation=GoogleReservation(
            locator=Locator(id=booking_response.booking_id),
            hotel_locators=[booking_response.reservation.locator],
            hotel_id=booking_response.reservation.hotel_id,
            start_date=booking_response.reservation.checkin,
            end_date=booking_response.reservation.checkout,
            customer=booking_response.reservation.customer,
            traveler=GoogleTraveler(
                first_name=booking_response.reservation.traveler.first_name,
                last_name=booking_response.reservation.traveler.last_name,
                occupancy=RoomParty(
                    adults=booking_response.reservation.traveler.occupancy.adults,
                    children=booking_request.traveler.occupancy.children,
                ),
            ),
            room_rate=booking_request.room_rate,
        ),
    )

    hotel_locators = booking_response.reservation.hotel_locator
    if hotel_locators:
        google_booking_response.reservation.hotel_locators.extend(hotel_locators)

    return google_booking_response


def convert_hotel_response(search_request: GoogleHotelSearchRequest, hotel: Hotel) -> GoogleHotelApiResponse:
    return GoogleHotelApiResponse(
        api_version=1,
        transaction_id=search_request.transaction_id,
        hotel_id=hotel.hotel_id,
        start_date=hotel.start_date,
        end_date=hotel.end_date,
        party=search_request.party,
        room_types=_get_room_types(hotel, search_request.language),
        rate_plans=_get_rate_plans(hotel),
        room_rates=_get_room_rates(hotel),
        hotel_details=_get_hotel_details(hotel),
    )


def _get_rate_plans(hotel: Hotel) -> List[GoogleRatePlan]:
    rate_plans = []
    for rate_plan in hotel.rate_plans:
        rate_plans.append(
            GoogleRatePlan(
                code=rate_plan.code,
                name=DisplayString(text=rate_plan.name, language="en"),
                description=DisplayString(text=rate_plan.description, language="en"),
                basic_amenities=_get_basic_amenity_mapping(rate_plan.amenities),
                guarantee_type=GuaranteeType.PAYMENT_CARD,
                cancellation_policy=_get_google_cancellation_policy(rate_plan.cancellation_policy, language="en"),
            )
        )

    return rate_plans


def _get_room_types(hotel: Hotel, language="en") -> List[GoogleRoomType]:
    room_types = []
    for room_type in hotel.room_types:
        room_types.append(
            GoogleRoomType(
                code=room_type.code,
                name=DisplayString(text=room_type.name, language=language),
                description=DisplayString(text=room_type.description, language=language),
                basic_amenities=BasicAmenities(free_breakfast=False, free_wifi=False, free_parking=False),
                photos=list(map(_get_image_mapping, room_type.photos)),
                capacity=RoomCapacity(adults=room_type.capacity.adults, children=room_type.capacity.children),
            )
        )

    return room_types


def _get_image_mapping(photo: Image) -> GoogleImage:
    return GoogleImage(url=photo.url, description=DisplayString(text="", language="en"))


def _get_basic_amenity_mapping(amenities: List[SimplenightAmenities]) -> BasicAmenities:
    has_free_parking = SimplenightAmenities.PARKING in amenities
    has_free_breakfast = SimplenightAmenities.BREAKFAST in amenities
    has_free_wifi = SimplenightAmenities.WIFI in amenities

    return BasicAmenities(free_breakfast=has_free_breakfast, free_wifi=has_free_wifi, free_parking=has_free_parking)


# TODO: Add descriptive text for images
def _get_photos(images: List[Image], language: str) -> List[GoogleImage]:
    return list(
        GoogleImage(url=image.url, description=DisplayString(text=image.type.value, language=language))
        for image in images
    )


# TODO: Actually implement cancellation policies
def _get_google_cancellation_policy(cancellation_policy: CancellationPolicy, language):
    return GoogleCancellationPolicy(
        summary=cancellation_policy.summary,
        cancellation_deadline=str(cancellation_policy.cancellation_deadline),
        unstructured_policy=DisplayString(text=cancellation_policy.unstructured_policy or "", language=language),
    )


def _get_room_rates(hotel: Hotel) -> List[GoogleRoomRate]:
    room_rates = []
    for room_rate in hotel.room_rates:
        capacity = room_rate.maximum_allowed_occupancy
        total_postpaid_fees = 0
        if room_rate.postpaid_fees:
            total_postpaid_fees = sum(x.amount.amount for x in room_rate.postpaid_fees.fees)

        room_rates.append(
            GoogleRoomRate(
                code=room_rate.code,
                room_type_code=room_rate.room_type_code,
                rate_plan_code=room_rate.rate_plan_code,
                maximum_allowed_occupancy=RoomCapacity(adults=capacity.adults, children=capacity.children),
                total_price_at_booking=room_rate.total,
                total_price_at_checkout=Money(amount=Decimal(total_postpaid_fees), currency=room_rate.total.currency),
                line_items=_get_line_items(room_rate),
                partner_data=[],
            )
        )

    return room_rates


def _get_line_items(room_rate: RoomRate) -> List[RoomRateLineItem]:
    def line_item(amount, line_item_type, checkout):
        return RoomRateLineItem(price=amount, type=line_item_type, paid_at_checkout=checkout)

    base_rate = line_item(room_rate.total_base_rate, LineItemType.BASE_RATE, False)
    taxes = line_item(room_rate.total_tax_rate, LineItemType.UNKNOWN_TAXES, False)

    line_items = [base_rate, taxes]
    if room_rate.postpaid_fees:
        for fee in room_rate.postpaid_fees.fees:
            line_items.append(line_item(fee.amount, fee.type, True))

    return line_items


def _get_hotel_details(hotel: Hotel) -> GoogleHotelDetails:
    return GoogleHotelDetails(
        name=hotel.hotel_details.name,
        address=hotel.hotel_details.address,
        geolocation=hotel.hotel_details.geolocation,
        phone_number=hotel.hotel_details.phone_number,
        email=hotel.hotel_details.email,
        photos=list(map(_get_image_mapping, hotel.hotel_details.photos)),
    )
