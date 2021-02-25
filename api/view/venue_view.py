from api.models.models import (
    Venue,
    VenueMedia,
    VenueContact,
    PaymentMethod,
    VenueDetail,
    ProductGroup,
    ProductsNightLifeMedia,
    ProductsNightLife,
    ProductHotel,
    ProductHotelsMedia,
    ProductsHotelRoomDetails,
    ProductsHotelRoomPricing,
)
from api.venue import serializers
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.auth.authentication import IsOwner
from api.utils.paginations import ObjectPagination
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin

from django_filters.rest_framework import DjangoFilterBackend


class VenueViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Venue.objects.filter()
    serializer_class = serializers.VenueSerializer
    pagination_class = ObjectPagination
    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ["get", "post", "put", "delete"]

    def perform_create(self, serializer):
        """Sets the user profile to the logged in User."""
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        if self.action == "delete":
            self.permission_classes = [
                IsOwner,
            ]
        elif self.action == "destroy":
            self.permission_classes = [IsOwner]
        elif self.action == "create":
            self.permission_classes = [IsOwner]

        return super(self.__class__, self).get_permissions()


class VenueMediaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = VenueMedia.objects.filter().order_by("order")
    serializer_class = serializers.VenueMediaSerializer
    pagination_class = ObjectPagination
    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ["get", "post", "put", "delete"]

    @action(detail=False, methods=["POST"], url_path="order", url_name="order")
    def order(self, request, parent_lookup_venue_id=None):
        orders = request.data.get("order", None)
        counter = 1
        for order in orders:
            self.queryset.filter(id=order).update(order=counter)
            counter += 1
        return Response({"response": "status updated"}, status=200)

    def modify_input_for_multiple_files(self, data, image, order):
        dict = {}
        dict["venue"] = data["venue_id"]
        dict["url"] = image
        if data.get("type", None):
            dict["type"] = data["type"]
        dict["order"] = order
        return dict

    # def create(self, request, *args, **kwargs):
    #     flag = 1
    #     arr = []
    #     if self.request.POST.get("venue_id", None) is not None:
    #         request.data._mutable = True

    #         order = self.queryset.filter(venue=self.request.POST["venue_id"])
    #         if order.exists():
    #             order = order.order_by("-created_at")
    #             order = order.first().order + 1

    #         urls = dict((request.data).lists())["url"]
    #         for url in urls:
    #             modified_data = self.modify_input_for_multiple_files(request.data, url, order)
    #             file_serializer = serializers.VenueMediaSerializer(data=modified_data)
    #             if file_serializer.is_valid():
    #                 file_serializer.save()
    #                 arr.append(file_serializer.data)
    #                 order += 1
    #             else:
    #                 flag = 0

    #     else:
    #         flag = 0

    #     if flag == 1:
    #         return Response(arr, status=status.HTTP_201_CREATED)
    #     else:
    #         return Response(arr, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        if self.request.POST.get("venue_id", None) is not None:
            request.data._mutable = True
            order = self.queryset.filter(venue=self.request.POST["venue_id"]).order_by("-created_at")

            if order.exists():
                request.POST._mutable = True
                order = order.first().order + 1
            else:
                order = 1
            request.data["order"] = order
            request.data["venue"] = self.request.POST["venue_id"]
            request.POST._mutable = False
            request = request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class VenueContactViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = VenueContact.objects.filter()
    serializer_class = serializers.VenueContactSerializer
    pagination_class = ObjectPagination
    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ["get", "post", "put", "delete"]


class VenueDetailViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = VenueDetail.objects.filter()
    serializer_class = serializers.VenueDetailSerializer
    pagination_class = ObjectPagination
    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ["get", "post", "put", "delete"]


class PaymentMethodViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = PaymentMethod.objects.filter()
    serializer_class = serializers.PaymentMethodSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]


class ProductGroupViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = ProductGroup.objects.filter().order_by("order")
    serializer_class = serializers.ProductGroupSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]

    @action(detail=False, methods=["POST"], url_path="order", url_name="order")
    def order(self, request, parent_lookup_venue_id=None):
        orders = request.data.get("order", None)
        counter = 1
        for order in orders:
            self.queryset.filter(id=order).update(order=counter)
            counter += 1
        return Response({"response": "status updated"}, status=200)

    def create(self, request, *args, **kwargs):
        if self.request.data.get("venue", None) is not None:
            request.POST._mutable = True

            order = self.queryset.filter(venue=self.request.data["venue"]).order_by("-created_at")
            if order.exists():
                request.POST._mutable = True
                order = order.first().order + 1
                request.data["order"] = order
                request.POST._mutable = False
                request = request

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductNightLifeMediaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = ProductsNightLifeMedia.objects.filter().order_by("order")
    serializer_class = serializers.ProductNightLifeMediaSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product_id"]

    @action(detail=False, methods=["POST"], url_path="order", url_name="order")
    def order(self, request, parent_lookup_venue_id=None):
        orders = request.data.get("order", None)
        counter = 1
        for order in orders:
            print(order)
            self.queryset.filter(id=order).update(order=counter)
            counter += 1
        return Response({"response": "status updated"}, status=200)

    def create(self, request, *args, **kwargs):
        if self.request.data.get("product", None) is not None:

            order = self.queryset.filter(product=self.request.data["product"]).order_by("-created_at")
            print(order)
            if order.exists():
                request.POST._mutable = True
                order = order.first().order + 1
                request.data["order"] = order
                request.POST._mutable = False
                request = request

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductNightLifeViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = ProductsNightLife.objects.filter().order_by("order")
    serializer_class = serializers.ProductsNightLifeSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]

    @action(detail=False, methods=["POST"], url_path="order", url_name="order")
    def order(self, request, parent_lookup_venue_id=None):
        orders = request.data.get("order", None)
        counter = 1
        for order in orders:
            self.queryset.filter(id=order).update(order=counter)
            counter += 1
        return Response({"response": "status updated"}, status=200)

    def create(self, request, *args, **kwargs):
        if self.request.data.get("venue", None) is not None:

            order = self.queryset.filter(venue=self.request.data["venue"]).order_by("-created_at")
            print(order)
            if order.exists():
                request.POST._mutable = True
                order = order.first().order + 1
                request.data["order"] = order
                request.POST._mutable = False
                request = request

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductHotelMediaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = ProductHotelsMedia.objects.filter()
    serializer_class = serializers.ProductHotelsMediaSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product_id"]

    @action(detail=False, methods=["POST"], url_path="order", url_name="order")
    def order(self, request, parent_lookup_venue_id=None):
        orders = request.data.get("order", None)
        counter = 1
        for order in orders:
            print(order)
            self.queryset.filter(id=order).update(order=counter)
            counter += 1
        return Response({"response": "status updated"}, status=200)

    def create(self, request, *args, **kwargs):
        if self.request.data.get("product", None) is not None:

            order = self.queryset.filter(product=self.request.data["product"]).order_by("-created_at")
            print(order)
            if order.exists():
                request.POST._mutable = True
                order = order.first().order + 1
                request.data["order"] = order
                request.POST._mutable = False
                request = request

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductHotelViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = ProductHotel.objects.filter().order_by("created_at")
    serializer_class = serializers.ProductHotelSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]

    @action(detail=False, methods=["POST"], url_path="order", url_name="order")
    def order(self, request, parent_lookup_venue_id=None):
        orders = request.data.get("order", None)
        counter = 1
        for order in orders:
            self.queryset.filter(id=order).update(order=counter)
            counter += 1
        return Response({"response": "status updated"}, status=200)

    def create(self, request, *args, **kwargs):
        if self.request.data.get("venue", None) is not None:

            order = self.queryset.filter(venue=self.request.data["venue"]).order_by("-created_at")
            print(order)
            if order.exists():
                request.POST._mutable = True
                order = order.first().order + 1
                request.data["order"] = order
                request.POST._mutable = False
                request = request

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductsHotelRoomPricingDetailsViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = ProductsHotelRoomPricing.objects.filter()
    serializer_class = serializers.ProductsHotelRoomPricingSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product_id"]
    permission_classes = [
        IsAuthenticated,
    ]


class ProductsHotelRoomDetailsViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = ProductsHotelRoomDetails.objects.filter()
    serializer_class = serializers.ProductsHotelRoomDetailsSerializer
    pagination_class = ObjectPagination
    # lookup_field = 'product_hotels'
    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ["get", "post", "put", "delete"]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product_id"]

    def filter_queryset(self, queryset):
        response = self.request.GET.get("product_id", None)
        if response == "" or response == "null":
            self.request.GET._mutable = True
            if response is not None:
                del self.request.GET["product_id"]

            self.request.GET._mutable = False
            queryset = queryset.filter(product_id__isnull=True)

        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
