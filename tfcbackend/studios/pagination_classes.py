from rest_framework import pagination


class StudioPagination(pagination.PageNumberPagination):
    page_size = 4


class ClassSchedulePagination(pagination.PageNumberPagination):
    page_size = 10


class UserClassSchedulePagination(pagination.PageNumberPagination):
    page_size = 4
