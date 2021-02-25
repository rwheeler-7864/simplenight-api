from enum import Enum

from rest_framework.views import exception_handler

from common.exceptions import AppException


class AppErrorCode(Enum):
    INVALID_API_KEY = "INVALID_API_KEY"
    INVALID_ORGANIZATION = "INVALID_ORGANIZATION"


class BookingErrorCode(Enum):
    PRICE_VERIFICATION = "PRICE_VERIFICATION"
    UNHANDLED_ERROR = "UNHANDLED_ERROR"
    CANCELLATION_FAILURE = "CANCELLATION_FAILURE"
    PROVIDER_BOOKING_FAILURE = "PROVIDER_BOOKING_FAILURE"
    PROVIDER_CANCELLATION_FAILURE = "PROVIDER_CANCELLATION_FAILURE"
    DUPLICATE_BOOKING = "DUPLICATE_BOOKING"
    MISMATCHED_CURRENCIES = "MISMATCHED_CURRENCIES"


class AvailabilityErrorCode(Enum):
    LOCATION_NOT_FOUND = "LOCATION_NOT_FOUND"
    HOTEL_NOT_FOUND = "HOTEL_NOT_FOUND"
    PROVIDER_ERROR = "PROVIDER_ERROR"


def handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response, and handle specific API errors
    if response is not None:
        response.data["status_code"] = response.status_code
        if isinstance(exc, BookingException):
            del response.data["detail"]
            response.data["error"] = {}
            response.data["error"]["type"] = exc.error_type.value
            response.data["error"]["message"] = exc.detail
    return response


class SimplenightApiException(AppException):
    def __init__(self, error_type, detail):
        super().__init__()
        self.error_type = error_type
        self.detail = detail

    def __repr__(self):
        return f"{self.__class__.__name__}: {self.error_type.name} - {self.detail}"


class AvailabilityException(SimplenightApiException):
    def __init__(self, detail: str, error_type: AvailabilityErrorCode):
        super().__init__(detail=detail, error_type=error_type)


class BookingException(SimplenightApiException):
    pass


class PaymentException(BookingException):
    pass
