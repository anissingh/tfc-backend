from django.urls import path
from subscriptions.views import SubscribeView, UpdateCardView, PaymentHistoryView,\
    FuturePaymentView, UpdatePaymentView, CancelPaymentView, GetSubscriptionView

app_name = 'subscriptions'

urlpatterns = [
    path('subscribe/<int:plan_id>/', SubscribeView.as_view()),
    path('update/card/', UpdateCardView().as_view()),
    path('user/<int:user_id>/payments/history/', PaymentHistoryView.as_view()),
    path('user/<int:user_id>/payments/future/', FuturePaymentView.as_view()),
    path('update/plan/<int:plan_id>/', UpdatePaymentView.as_view()),
    path('cancel/', CancelPaymentView.as_view()),
    path('plans/all/', GetSubscriptionView.as_view()),
]
