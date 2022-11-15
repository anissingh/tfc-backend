from rest_framework import serializers
from subscriptions.models import Payment, SubscriptionPlan, Card


class SubscriptionPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'amount']


class CardSerializer(serializers.ModelSerializer):

    class Meta:
        model = Card
        fields = ['holder_name', 'number']


class PaymentSerializer(serializers.ModelSerializer):

    subscription_plan = SubscriptionPlanSerializer()
    card_used = CardSerializer()

    class Meta:
        model = Payment
        fields = ['subscription_plan', 'card_used', 'date_and_time']
