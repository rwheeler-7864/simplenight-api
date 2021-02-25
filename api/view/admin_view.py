from rest_framework import viewsets
from api.auth.authentication import APIAdminPermission
from api.accounts.serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response
from api.utils.paginations import ObjectPagination
from rest_framework import status


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [APIAdminPermission]
    queryset = User.objects.filter()
    serializer_class = UserSerializer
    pagination_class = ObjectPagination
    http_method_names = ["get", "post", "put", "delete"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data={"reponse": "object deleted now"}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(id=self.request.user.id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data
        if not data.get("is_staff", None):
            data["is_staff"] = True
            data = data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
