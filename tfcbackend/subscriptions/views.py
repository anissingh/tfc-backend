from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from subscriptions.models import SubscriptionPlan, UserSubscription, Card, Payment
from accounts.models import User
from subscriptions.serializers import PaymentSerializer, SubscriptionPlanSerializer
from datetime import datetime
from django.utils.timezone import localdate
from subscriptions.utils import make_payment, calculate_next_payment_day, get_curr_datetime
from studios.models import ClassInstance


# Create your views here.
class GetSubscriptionView(ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    model = SubscriptionPlan
    paginate_by = 50

    def get_queryset(self):
        return SubscriptionPlan.objects.all()


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        subscription_plan = get_object_or_404(SubscriptionPlan, id=self.kwargs['plan_id'])
        # Get payload data
        email = request.data.get('email', '')
        card_number = request.data.get('card_number', '')
        cardholder_name = request.data.get('cardholder_name', '')
        expiration_date_str = request.data.get('expiration_date', '')
        cvv = request.data.get('cvv', '')

        # Validate request
        if not User.objects.filter(email=email).exists():
            return Response({
                'status': 'no user with this email exists'
            }, status=400)

        user = User.objects.get(email=email)
        # Check if user already has a subscription (cancelled or not)
        if UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'a subscription is currently active. update subscription instead'
            }, status=400)

        # If no subscription exists, try to create card
        result = _create_card(card_number, cardholder_name, expiration_date_str, cvv)
        if result[1] != 'success':
            return Response({
                result[0]: result[1]
            }, status=400)

        card = result[2]
        # Create user subscription object
        curr_date = localdate()
        next_payment_day = calculate_next_payment_day(curr_date, subscription_plan)
        user_subscription = UserSubscription(user=user, amount=subscription_plan.amount,
                                             payment_card=card, next_payment_day=next_payment_day,
                                             subscription_plan=subscription_plan)
        user_subscription.save()

        # Make first payment
        make_payment(user_subscription)

        return Response({
            'status': 'success'
        })


class UpdateCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Payload
        email = request.data.get('email', '')
        card_number = request.data.get('card_number', '')
        cardholder_name = request.data.get('cardholder_name', '')
        expiration_date_str = request.data.get('expiration_date', '')
        cvv = request.data.get('cvv', '')

        # Validate request
        if not User.objects.filter(email=email).exists():
            return Response({
                'status': 'no user with this email exists'
            }, status=400)

        user = User.objects.get(email=email)
        # If user does not have a subscription already, tell them to subscribe first
        if not UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'no subscription detected. subscribe and set card upon subscription'
            }, status=400)

        # Otherwise, try to create card
        result = _create_card(card_number, cardholder_name, expiration_date_str, cvv)
        if result[1] == 'success':
            # If we make it here, card was created and saved
            card = result[2]
            user_subscription = UserSubscription.objects.get(user=user)
            user_subscription.payment_card = card
            user_subscription.save()

        response_code = 200 if result[1] == 'success' else 400
        return Response({
            result[0]: result[1]
        }, status=response_code)


class PaymentHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    model = Payment
    paginate_by = 100

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        # curr_dt = get_curr_datetime()
        # payments = Payment.objects.filter(user=user, date_and_time__lt=curr_dt)
        # Only need to filter for user because payment objects only exist if a payment
        # was made in the past
        payments = Payment.objects.filter(user=user)
        return payments.order_by('date_and_time')


class FuturePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')

        # Validate request
        if not User.objects.filter(email=email).exists():
            return Response({
                'status': 'no user with this email exists'
            }, status=400)

        user = User.objects.get(email=email)

        # If the user has not subscribed, they have no future payments
        if not UserSubscription.objects.filter(user=user).exists():
            return Response({})

        # If the user's subscription is cancelled, return a message telling them that
        user_subscription = UserSubscription.objects.get(user=user)
        if not user_subscription.subscription_plan:
            return Response({
                'status': 'subscription cancelled'
            })

        # Otherwise, get next payment info and return it
        payment_info = {
            'next_payment_day': user_subscription.next_payment_day,
            'amount': user_subscription.amount,
            'card_number': user_subscription.payment_card.number,
            'recurrence': user_subscription.subscription_plan.get_frequency_display()
        }

        return Response({
            'status': 'success',
            'payment_info': payment_info
        })


class UpdatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        subscription_plan = get_object_or_404(SubscriptionPlan, id=self.kwargs['plan_id'])

        # Payload
        email = request.data.get('email', '')

        # Validate request
        if not User.objects.filter(email=email).exists():
            return Response({
                'status': 'no user with this email exists'
            }, status=400)

        user = User.objects.get(email=email)

        if not UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'user has not subscribed yet'
            }, status=400)

        # Update subscription plan
        user_subscription = UserSubscription.objects.get(user=user)
        user_subscription.subscription_plan = subscription_plan
        user_subscription.amount = subscription_plan.amount
        user_subscription.save()

        return Response({
            'status': 'success'
        })


class CancelPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')

        # Validate request
        if not User.objects.filter(email=email).exists():
            return Response({
                'status': 'no user with this email exists'
            }, status=400)

        user = User.objects.get(email=email)

        if not UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'user has not subscribed yet'
            }, status=400)

        # Cancel subscription plan
        user_subscription = UserSubscription.objects.get(user=user)
        if user_subscription.subscription_plan is None:
            return Response({
                'status': 'subscription plan already cancelled'
            }, status=400)
        user_subscription.subscription_plan = None
        user_subscription.save()

        # Note: User gets unenrolled when next payment is made. This is because the user
        # may want to re-subscribe, so it does not make sense to unenroll the user before
        # their subscription is officially over.

        return Response({
            'status': 'success'
        })


def _create_card(card_number, cardholder_name, expiration_date_str, cvv):
    try:
        expiration_date = datetime.strptime(expiration_date_str, '%m-%Y').date()
    except ValueError:
        expiration_date = ''

    # Make sure all card parameters were present
    required_params = {card_number, cardholder_name, expiration_date, cvv}
    if '' in required_params:
        return ('status', 'card information is invalid', None)

    # Otherwise, create a new card with their card info
    try:
        card = Card(number=card_number, holder_name=cardholder_name,
                    expiration_date=expiration_date, cvv=cvv)
        card.save()
        return ('status', 'success', card)
    except ValidationError:
        return ('status', 'card information is invalid', None)
