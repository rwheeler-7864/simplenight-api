import xmltodict
import json

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from django.http import HttpResponse

from api.urban.urban_service import UrbanService

urban_service = UrbanService()

class UrbanViewSet(viewsets.ViewSet):
    def xml_to_json(self, response):
        dict_response = xmltodict.parse(response.content)
        json_response = json.dumps(dict_response, indent=2)
        return json_response

    @action(detail=False, url_path="get_standard_countries", methods=["GET"], name="Get the standard list of countries")
    def get_standard_countries(self, request: Request):
        response = urban_service.get_standard_countries(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_ua_countries", methods=["GET"], name="Get list of available countries in Urban Adventures network")
    def get_ua_countries(self, request: Request):
        response = urban_service.get_ua_countries(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_ua_destinations", methods=["GET"], name="Get list of destinations of a certain country")
    def get_ua_destinations(self, request: Request):
        response = urban_service.get_ua_destinations(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_trips", methods=["GET"], name="Get list of trips of a certain destinations")
    def get_trips(self, request: Request):
        response = urban_service.get_trips(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")
    
    @action(detail=False, url_path="get_trip_info", methods=["GET"], name="Get full information of a trip")
    def get_trip_info(self, request: Request):
        response = urban_service.get_trip_info(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_trip_alm", methods=["GET"], name="Get number of alloment of a specific date of a trip mentioned in request")
    def get_trip_alm(self, request: Request):
        response = urban_service.get_trip_alm(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_trip_price", methods=["GET"], name="Get price detail of a specific trip on a departure date")
    def get_trip_price(self, request: Request):
        response = urban_service.get_trip_price(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_trip_avail_date", methods=["GET"], name="Get list of dates having allotment of a trip mentioned in request")
    def get_trip_avail_date(self, request: Request):
        response = urban_service.get_trip_avail_date(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_trip_availabilities", methods=["GET"], name="Get allotment and price info for a date range of a trip mentioned in request")
    def get_trip_availabilities(self, request: Request):
        response = urban_service.get_trip_availabilities(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="book_trip", methods=["GET"], name="Book a trip in UA system")
    def book_trip(self, request: Request):
        response = urban_service.book_trip(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="cancel_booking", methods=["GET"], name="Submit a cancel booking request")
    def cancel_booking(self, request: Request):
        response = urban_service.cancel_booking(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_booking_voucher", methods=["GET"], name="Get the URL to download UA booking voucher")
    def get_booking_voucher(self, request: Request):
        response = urban_service.get_booking_voucher(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_booking_info", methods=["GET"], name="Get booking info")
    def get_booking_info(self, request: Request):
        response = urban_service.get_booking_info(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")

    @action(detail=False, url_path="get_exchange_rate_list", methods=["GET"], name="Get exchange rate")
    def get_exchange_rate_list(self, request: Request):
        response = urban_service.get_exchange_rate_list(request)
        return HttpResponse(self.xml_to_json(response), content_type="application/json")