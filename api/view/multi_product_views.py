from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.request import Request

from api.activities.activity_models import SimplenightActivityDetailRequest, SimplenightActivityVariantRequest
from api.auth.authentication import HasOrganizationAPIKey, OrganizationApiDailyThrottle, OrganizationApiBurstThrottle
from api.common.common_models import from_json
from api.booking import booking_service
from api.hotel.models.booking_model import MultiProductBookingRequest
from api.multi import multi_product
from api.multi.multi_product_models import SearchRequest
from api.view.default_view import _response


class AllProductsViewSet(viewsets.ViewSet):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (HasOrganizationAPIKey,)
    throttle_classes = (OrganizationApiDailyThrottle, OrganizationApiBurstThrottle)

    @action(detail=False, url_path="search", methods=["POST"], name="Search All Products")
    def search(self, request: Request):
        request = from_json(request.data, SearchRequest)
        results = multi_product.search_request(request)

        return _response(results)

    @action(detail=False, url_path="details", methods=["POST"], name="Activity Details")
    def details(self, request: Request):
        request = from_json(request.data, SimplenightActivityDetailRequest)
        results = multi_product.details(request)

        return _response(results)

    @action(detail=False, url_path="variants", methods=["POST"], name="Activity Variants")
    def variants(self, request: Request):
        request = from_json(request.data, SimplenightActivityVariantRequest)
        results = multi_product.variants(request)

        return _response(results)

    @action(detail=False, url_path="book", methods=["POST"], name="Create a Booking")
    def book(self, request: Request):
        request = from_json(request.data, MultiProductBookingRequest)
        results = booking_service.book(request)

        return _response(results)
