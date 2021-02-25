from rest_framework.pagination import PageNumberPagination

class ObjectPagination(PageNumberPagination):
    page_size = 30
