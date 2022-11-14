from rest_framework import serializers
from subscriptions.models import Payment, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'amount']


class PaymentSerializer(serializers.ModelSerializer):

    subscription_plan = SubscriptionPlanSerializer()

    class Meta:
        model = Payment
        fields = ['subscription_plan', 'card_used', 'date_and_time']
