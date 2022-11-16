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

    card_used = CardSerializer()

    class Meta:
        model = Payment
        fields = ['amount', 'card_used', 'date_and_time']
