from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from api.locations import location_service
from api.view.default_view import _response


class LocationsViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    @action(detail=False, url_path="cities", methods=["GET"], name="Search Locations by Prefix")
    def find_all(self, request: Request):
        lang_code = request.GET.get("lang_code")
        country_code = request.GET.get("country_code")

        return _response(location_service.find_all_cities(country_code=country_code, language_code=lang_code))

    @action(detail=False, url_path="prefix", methods=["GET"], name="Search Locations by Prefix")
    def find_by_prefix(self, request: Request):
        lang_code = request.GET.get("lang_code", "en")
        prefix = request.GET.get("prefix")

        locations = location_service.find_by_prefix(prefix, lang_code)
        return _response(locations)

    @action(detail=False, url_path="id", methods=["GET"], name="Search Locations by Prefix")
    def find_by_id(self, request: Request):
        lang_code = request.GET.get("lang_code", "en")
        geoname_id = request.GET.get("location_id")

        locations = location_service.find_city_by_simplenight_id(geoname_id, lang_code)
        return _response(locations)
