from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from subscriptions.models import SubscriptionPlan, UserSubscription, Card, Payment
from accounts.models import User
from subscriptions.serializers import PaymentSerializer
from datetime import datetime
from django.utils.timezone import localdate
from subscriptions.utils import make_payment, calculate_next_payment_day, get_curr_datetime
from studios.models import ClassInstance

# TODO: User IS ALLOWED to be in classes on the day of cancellation to prevent users being mad
# TODO: about paying at 6pm so they should be able to attend classes until 6pm on cancellation date


# Create your views here.
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
            })

        user = User.objects.get(email=email)
        # Check if user already has a subscription
        if UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'subscription already exists. update subscription instead'
            })

        # If no subscription exists, try to create card
        result = _create_card(card_number, cardholder_name, expiration_date_str, cvv)
        if result[1] != 'success':
            return Response({
                result[0]: result[1]
            })

        card = result[2]
        # Create user subscription object
        curr_date = localdate()
        next_payment_day = calculate_next_payment_day(curr_date, subscription_plan)
        user_subscription = UserSubscription(user=user,
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
            })

        user = User.objects.get(email=email)
        # If user does not have a subscription already, tell them to subscribe first
        if not UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'no subscription detected. subscribe and set card upon subscription'
            })

        # Otherwise, try to create card
        result = _create_card(card_number, cardholder_name, expiration_date_str, cvv)
        if result[1] == 'success':
            # If we make it here, card was created and saved
            card = result[2]
            user_subscription = UserSubscription.objects.get(user=user)
            user_subscription.payment_card = card
            user_subscription.save()
        return Response({
            result[0]: result[1]
        })


# TODO: Test
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
            })

        user = User.objects.get(email=email)

        # If the user has not subscribed, they have no future payments
        if not UserSubscription.objects.filter(user=user).exists():
            return Response({})

        # Otherwise, get next payment info and return it
        user_subscription = UserSubscription.objects.get(user=user)
        payment_info = {
            'next_payment_day': user_subscription.next_payment_day,
            'plan': user_subscription.subscription_plan.name,
            'cancelled': user_subscription.cancelled
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
            })

        user = User.objects.get(email=email)

        if not UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'user has not subscribed yet'
            })

        # Update subscription plan
        user_subscription = UserSubscription.objects.get(user=user)
        user_subscription.subscription_plan = subscription_plan
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
            })

        user = User.objects.get(email=email)

        if not UserSubscription.objects.filter(user=user).exists():
            return Response({
                'status': 'user has not subscribed yet'
            })

        # Cancel subscription plan
        user_subscription = UserSubscription.objects.get(user=user)
        billing_end_day = user_subscription.next_payment_day
        user_subscription.delete()

        # Un-enroll user in any classes they are enrolled in after their billing period ends
        all_enrolled_classes = user.enrolled_classes.all()
        enrolled_after_billing = all_enrolled_classes.filter(date__gt=billing_end_day)
        for class_instance in enrolled_after_billing:
            user.enrolled_classes.remove(class_instance)
            class_instance.enrolled -= 1
            class_instance.save()

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

