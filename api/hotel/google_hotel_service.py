from api.hotel import core_hotel_service, converter
from api.booking import booking_service
from api.hotel.converter.google_models import (
    GoogleHotelSearchRequest,
    GoogleHotelApiResponse,
    GoogleBookingSubmitRequest,
)


def search_by_id(google_search_request: GoogleHotelSearchRequest) -> GoogleHotelApiResponse:
    search_request = converter.google.convert_hotel_specific_search(google_search_request)
    hotel = core_hotel_service.search_by_id(search_request)
    return converter.google.convert_hotel_response(google_search_request, hotel)


def booking(google_booking_request: GoogleBookingSubmitRequest):
    booking_request = converter.google.convert_booking_request(google_booking_request)
    booking_response = booking_service.book_hotel(booking_request)

    return converter.google.convert_booking_response(google_booking_request, booking_response)
