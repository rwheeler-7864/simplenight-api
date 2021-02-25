from decimal import Decimal, ROUND_UP, getcontext
from typing import List, Union, Dict, Optional

from api.hotel.models.hotel_common_models import Money, RoomRate, HotelReviews
from api.hotel import core_hotel_service
from api.hotel.models.hotel_api_model import (
    HotelDetails,
    HotelSpecificSearch,
    AdapterHotel,
    HotelLocationSearch,
    HotelDetailsSearchRequest,
    Hotel,
    SimplenightRoomType,
    RoomType,
    RatePlan,
    SimplenightHotel,
    HotelBatchSearch,
)


def search_by_location(search_request: HotelLocationSearch) -> List[SimplenightHotel]:
    """
    Converts hotels from the Core Hotel Service into
    a format suitable for the Simplenight Front End
    """

    hotels = core_hotel_service.search_by_location(search_request)
    return list(map(_convert_hotel_to_front_end_format, hotels))


def search_by_id(search_request: HotelSpecificSearch) -> SimplenightHotel:
    hotel = core_hotel_service.search_by_id(search_request)
    return _convert_hotel_to_front_end_format(hotel)


def search_by_id_batch(search_request: HotelBatchSearch) -> List[SimplenightHotel]:
    hotels = core_hotel_service.search_by_id_batch(search_request)
    return list(map(_convert_hotel_to_front_end_format, hotels))


def details(hotel_details_req: HotelDetailsSearchRequest) -> HotelDetails:
    return core_hotel_service.details(hotel_details_req)


def recheck(provider: str, room_rate: RoomRate) -> RoomRate:
    return core_hotel_service.recheck(provider, room_rate)


def reviews(simplenight_hotel_id: str) -> HotelReviews:
    return core_hotel_service.reviews(simplenight_hotel_id)


def _get_nightly_rate(hotel: Union[Hotel, AdapterHotel], amount: Decimal):
    room_nights = max((hotel.end_date - hotel.start_date).days, 1)

    getcontext().rounding = ROUND_UP
    return Decimal(round(amount / room_nights, 2))


def _convert_hotel_to_front_end_format(hotel: Hotel) -> Optional[SimplenightHotel]:
    if hotel is None:
        return None

    room_types: Dict[str, RoomType] = {room_type.code: room_type for room_type in hotel.room_types}
    rate_plans: Dict[str, RatePlan] = {rate_plan.code: rate_plan for rate_plan in hotel.rate_plans}

    simplenight_room_types = []
    for room_rate in hotel.room_rates:
        room_type = room_types[room_rate.room_type_code]
        rate_plan = rate_plans[room_rate.rate_plan_code]

        simplenight_room_type = SimplenightRoomType(
            code=room_rate.code,
            name=room_type.name,
            description=room_type.description,
            amenities=room_type.amenities,
            photos=room_type.photos,
            capacity=room_type.capacity,
            bed_types=room_type.bed_types,
            total_base_rate=room_rate.total_base_rate,
            total_tax_rate=room_rate.total_tax_rate,
            total=room_rate.total,
            rate_type=room_rate.rate_type,
            cancellation_policy=rate_plan.cancellation_policy,
            daily_rates=room_rate.daily_rates,
            unstructured_policies=room_type.unstructured_policies,
            postpaid_fees=room_rate.postpaid_fees,
            avg_nightly_rate=Money(
                amount=_get_nightly_rate(hotel, room_rate.total.amount), currency=room_rate.total.currency
            ),
        )

        simplenight_room_types.append(simplenight_room_type)

    simplenight_hotel = SimplenightHotel(
        hotel_id=hotel.hotel_id,
        start_date=hotel.start_date,
        end_date=hotel.end_date,
        hotel_details=hotel.hotel_details,
        room_types=simplenight_room_types,
        avg_nightly_rate=hotel.average_nightly_rate,
        avg_nightly_base=hotel.average_nightly_base,
        avg_nightly_tax=hotel.average_nightly_tax,
        occupancy=hotel.occupancy,
    )

    if hotel.error:
        simplenight_hotel.error = hotel.error

    return simplenight_hotel
