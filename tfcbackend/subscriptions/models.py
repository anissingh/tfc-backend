from django.core.exceptions import ValidationError
from django.db import models
from accounts.models import User
from django.utils.timezone import localdate

# TODO: Do not allow users to drop/enroll classes without a subscription


# Create your models here.
class SubscriptionPlan(models.Model):
    FREQUENCY = (
        (0, 'Weekly'),
        (1, 'Bi-Weekly'),
        (2, 'Monthly'),
        (3, 'Every 3 Months'),
        (4, 'Every 6 Months'),
        (5, 'Yearly'),
    )

    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    frequency = models.IntegerField(choices=FREQUENCY)
    description = models.TextField()

    def clean(self):
        super().clean()
        errors = {}
        if self.amount < 0:
            errors['amount'] = 'Amount must be non-negative.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    def __str__(self):
        return f'{self.name}: ${self.amount}'

    class Meta:
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'


class Card(models.Model):
    number = models.CharField(max_length=19)
    holder_name = models.CharField(max_length=200)
    expiration_date = models.DateField()
    cvv = models.CharField(max_length=3)

    def clean(self):
        super().clean()
        errors = {}
        if len(self.number) < 13:
            errors['number'] = 'Card number too short'
        if len(self.cvv) < 3:
            errors['cvv'] = 'CVV too short'
        if self.expiration_date < localdate():
            errors['expiration_date'] = 'Card has expired'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    class Meta:
        verbose_name = 'Card'
        verbose_name_plural = 'Cards'


class UserSubscription(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    payment_card = models.ForeignKey(to=Card, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(to=SubscriptionPlan, on_delete=models.CASCADE)
    next_payment_day = models.DateField()

    def __str__(self):
        return f'Subscription: {self.user.name} to {self.subscription_plan.name}'

    class Meta:
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'


# TODO: subscription_plan CASCADE seems wrong? (if subscription_plan gets deleted, payment
# TODO: should stick around)
class Payment(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    card_used = models.ForeignKey(to=Card, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(to=SubscriptionPlan, on_delete=models.CASCADE)
    date_and_time = models.DateTimeField()

    def __str__(self):
        return f'{self.user.name} paid {self.subscription_plan.amount} on {self.date_and_time}'

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
