from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from django.http import HttpResponse
import json

from api.charging.charging_service import ChargingService

charging_service = ChargingService()

class ChargingViewSet(viewsets.ViewSet):
    @action(detail=False, url_path="poi", methods=["GET"], name="Search charging location")
    def get_poi(self, request: Request):
        if not(request.GET.get("latitude") and request.GET.get("longitude")):
            error_message = {
                "message": "Latitude and longitude are required"
            }
            return HttpResponse(json.dumps(error_message), content_type="application/json", status=400)
            
        response = charging_service.get_poi(request)
        filtered_response = list(map((lambda x: {
            "ID": x["ID"],
            "UUID": x["UUID"],
            "UserComments": x["UserComments"],
            "MediaItems": x["MediaItems"],
            "UsageType": x["UsageType"],
            "StatusType": x["StatusType"],
            "UsageCost": x["UsageCost"],
            "AddressInfo": x["AddressInfo"],
            "NumberOfPoints": x["NumberOfPoints"],
            "GeneralComments": x["GeneralComments"],
            "Connections": x["Connections"],
        }), response.json()))
        return HttpResponse(json.dumps(filtered_response), content_type="application/json")

    @action(detail=False, url_path="reference_data", methods=["GET"], name="Get reference data")
    def get_reference(self, request: Request):
        response = charging_service.get_reference(request)
        return HttpResponse(response, content_type="application/json")

    @action(detail=False, url_path="address", methods=["GET"], name="Get address")
    def get_address(self, request: Request):
        if not(request.GET.get("latitude") and request.GET.get("longitude")):
            error_message = {
                "message": "Latitude and longitude are required"
            }
            return HttpResponse(json.dumps(error_message), content_type="application/json", status=400)   
             
        response = charging_service.get_address(request)
        return HttpResponse(response, content_type="application/json")

    @action(detail=False, url_path="comment", methods=["POST"], name="Post comment")
    def post_comment(self, request: Request):
        response = charging_service.post_comment(request)
        return HttpResponse(response, content_type="application/json")
