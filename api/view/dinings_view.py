from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
import json
import decimal

from api.common.common_models import from_json
from api.view.default_view import _response
from api.dining.models.dining_api_model import (
  DiningSearch,
  OpeningSearch,
  IdSearch,
  DiningReservationRequest,
  AdapterCancelRequest
)
from api.dining import dining_service 


class DiningViewSet(viewsets.ViewSet):
    @action(detail=False, url_path="search", methods=["POST"], name="Search businesses")
    def search_businesses(self, request: Request):
        request = from_json(request.data, DiningSearch)
        businesses = dining_service.get_businesses(request)
        
        return _response(businesses)

    @action(detail=False, url_path="available-times", methods=["POST"], name="Get available times")
    def get_openings(self, request: Request):
        request = from_json(request.data, OpeningSearch)
        openings = dining_service.get_openings(request)
        
        return _response(openings)

    @action(detail=False, url_path="search-by-id", methods=["POST"], name="Get dining detail")
    def get_business(self, request: Request):
        request = from_json(request.data, IdSearch)
        openings = dining_service.details(request)
        
        return _response(openings)

    @action(detail=False, url_path="reviews", methods=["POST"], name="Get reviews by id")
    def get_reviews(self, request: Request):
        request = from_json(request.data, IdSearch)
        reviews = dining_service.reviews(request)
        
        return _response(reviews)

    @action(detail=False, url_path="booking", methods=["POST"], name="Creates a booking")
    def create_booking(self, request: Request):
        request = from_json(request.data, DiningReservationRequest)
        response = dining_service.book(request)
        
        return _response(response)

    @action(detail=False, url_path="cancel-booking", methods=["POST"], name="Cancel a booking")
    def cancel_booking(self, request: Request):
        dining_service.cancel(booking_id=request.data['booking_id'])
        
        return HttpResponse('')

