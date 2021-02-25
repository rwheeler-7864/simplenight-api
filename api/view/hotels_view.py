from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from api import logger
from api.auth.authentication import HasOrganizationAPIKey, OrganizationApiDailyThrottle, OrganizationApiBurstThrottle
from api.booking import booking_service
from api.common.common_models import from_json
from api.common.request_cache import get_request_cache
from api.hotel import hotel_service, google_hotel_service
from api.hotel.adapters.priceline.priceline_sales_report import PricelineSalesReport
from api.hotel.converter.google_models import GoogleHotelSearchRequest, GoogleBookingSubmitRequest
from api.hotel.google_pricing import google_pricing_api
from api.hotel.models.booking_model import HotelBookingRequest
from api.hotel.models.hotel_api_model import HotelLocationSearch, HotelSpecificSearch, CancelRequest, HotelBatchSearch
from api.management import google_reconciliation
from api.view.default_view import _response


class HotelViewSet(viewsets.ViewSet):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (HasOrganizationAPIKey,)
    throttle_classes = (OrganizationApiDailyThrottle, OrganizationApiBurstThrottle)

    @action(detail=False, url_path="search-by-location", methods=["GET", "POST"], name="Search Hotels")
    def search_by_location(self, request: Request):
        request = from_json(request.data, HotelLocationSearch)
        hotels = hotel_service.search_by_location(request)

        return _response(hotels)

    @action(detail=False, url_path="search-by-id", methods=["GET", "POST"], name="Search Hotels")
    def search_by_id(self, request):
        request = from_json(request.data, HotelSpecificSearch)
        hotels = hotel_service.search_by_id(request)

        return _response(hotels)

    @action(detail=False, url_path="search-by-id-batch", methods=["POST"], name="Search Hotels by ID Batch")
    def search_by_id_batch(self, request):
        request = from_json(request.data, HotelBatchSearch)
        hotels = hotel_service.search_by_id_batch(request)

        return _response(hotels)

    @action(detail=False, url_path="google/search-by-id", methods=["GET", "POST"], name="Search Hotels Google API")
    def search_by_id_google(self, request):
        google_search_request = from_json(request.data, GoogleHotelSearchRequest)
        google_search_response = google_hotel_service.search_by_id(google_search_request)

        return _response(google_search_response)

    @action(detail=False, url_path="reviews", methods=["GET"], name="Hotel User Reviews")
    def reviews(self, request):
        simplenight_hotel_id = request.GET.get("hotel_id")
        reviews = hotel_service.reviews(simplenight_hotel_id)
        if reviews:
            return _response(reviews)
        else:
            raise NotFound(detail="Could not find user reviews for hotel ID: " + simplenight_hotel_id)

    @action(detail=False, url_path="booking", methods=["POST"], name="Hotel Booking")
    def booking(self, request):
        booking_request = from_json(request.data, HotelBookingRequest)
        booking_response = booking_service.book_hotel(booking_request)

        return _response(booking_response)

    @action(detail=False, url_path="cancel", methods=["POST"], name="Cancel Booking")
    def cancel_lookup(self, request):
        cancel_request = from_json(request.data, CancelRequest)
        cancel_response = booking_service.cancel_lookup(cancel_request)

        return _response(cancel_response)

    @action(detail=False, url_path="cancel-confirm", methods=["POST"], name="Confirm Cancel Booking")
    def cancel_confirm(self, request):
        cancel_request = from_json(request.data, CancelRequest)
        cancel_response = booking_service.cancel_confirm(cancel_request)

        return _response(cancel_response)

    @action(detail=False, url_path="google/booking", methods=["POST"], name="GoogleHotel Booking")
    def booking_google(self, request):
        google_booking_request = from_json(request.data, GoogleBookingSubmitRequest)
        return _response(google_hotel_service.booking(google_booking_request))

    @action(detail=False, url_path="google/pricing", methods=["POST"], name="GoogleHotel Pricing API")
    def google_live_pricing(self, request):
        logger.info(f"Google Live Pricing API Request: {bytes.decode(request.body, 'utf-8')}")
        results = google_pricing_api.live_pricing_api(request.body)
        return HttpResponse(results, content_type="text/xml")

    @action(detail=False, url_path="google/properties", methods=["GET"], name="GoogleHotel Property API")
    def properties(self, request):
        provider = request.GET.get("provider", None)
        if not provider:
            provider = "giata"

        results = google_pricing_api.generate_property_list(request.GET.get("country_codes"), provider_name=provider)
        return HttpResponse(results, content_type="text/xml")

    @action(
        detail=False,
        url_path="google/properties/hotel-codes",
        methods=["POST"],
        name="Property API by Hotel Code",
    )
    def properties_hotel_codes(self, request):
        hotel_codes = request.data
        results = google_pricing_api.generate_property_list_hotel_codes(hotel_codes)

        return HttpResponse(results, content_type="text/xml")

    @action(detail=False, url_path="google/reconciliation", methods=["GET"], name="GoogleAds Commission Report")
    def reconciliation(self, request):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        organization = request.GET.get("organization")

        results = google_reconciliation.get_report(organization, start_date, end_date)
        return HttpResponse(google_reconciliation.format_report_csv(results), content_type="text/plain")

    @action(detail=False, url_path="priceline/ghost-booking", methods=["GET"], name="Priceline Ghost Bookings Report")
    def reconciliation(self, *_):
        report = PricelineSalesReport()
        return _response(report.find_unmatched_bookings())

    @action(detail=False, url_path="status", methods=["GET"], name="Health Check")
    def status(self, _):
        """Simply sets a variable in LocMem request cache, and retrieves it, to ensure things are working"""
        request_cache = get_request_cache()
        organization = request_cache.get("organization")
        organization_name = organization.name
        request_cache.set("__status", f"OK {organization_name}")

        return Response(data=request_cache.get("__status"))