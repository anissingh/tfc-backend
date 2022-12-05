from rest_framework import pagination


class SubscriptionPlanPagination(pagination.PageNumberPagination):
    page_size = 3

