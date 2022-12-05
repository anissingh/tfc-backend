from rest_framework import serializers
from subscriptions.models import Payment, SubscriptionPlan, Card


class SubscriptionPlanSerializer(serializers.ModelSerializer):

    frequency = serializers.CharField(source='get_frequency_display')

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'amount', 'frequency']


class SubscriptionPlanDescriptionSerializer(serializers.ModelSerializer):
    frequency = serializers.CharField(source='get_frequency_display')

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'amount', 'frequency', 'description']


class CardSerializer(serializers.ModelSerializer):

    expiration_date = serializers.DateField()

    class Meta:
        model = Card
        fields = ['holder_name', 'number', 'expiration_date', 'cvv']


class PaymentSerializer(serializers.ModelSerializer):

    card_used = CardSerializer()

    class Meta:
        model = Payment
        fields = ['amount', 'card_used', 'date_and_time']
