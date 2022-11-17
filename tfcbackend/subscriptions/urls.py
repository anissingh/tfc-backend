from django.urls import path
from subscriptions.views import SubscribeView, UpdateCardView, PaymentHistoryView,\
    FuturePaymentView, UpdatePaymentView, CancelPaymentView, GetSubscriptionView

app_name = 'subscriptions'

urlpatterns = [
    path('subscribe/<int:plan_id>/', SubscribeView.as_view()),
    path('update-card/', UpdateCardView().as_view()),
    path('payment-history/<int:user_id>/', PaymentHistoryView.as_view()),
    path('future-payments/<int:user_id>/', FuturePaymentView.as_view()),
    path('update/<int:plan_id>/', UpdatePaymentView.as_view()),
    path('cancel/', CancelPaymentView.as_view()),
    path('plans/all/', GetSubscriptionView.as_view()),
]
