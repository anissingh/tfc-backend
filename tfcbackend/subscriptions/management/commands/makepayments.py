from django.core.management.base import BaseCommand
from subscriptions.models import UserSubscription
from subscriptions.utils import make_payment
from django.utils.timezone import localdate


class Command(BaseCommand):
    help = 'Charges users whose subscriptions are due today.'

    def handle(self, *args, **options):
        self.stdout.write('Running command makepayments...')
        curr_date = localdate()
        subscriptions_due = UserSubscription.objects.filter(next_payment_day=curr_date)
        for user_subscription in subscriptions_due:
            # Make payment
            make_payment(user_subscription)

        self.stdout.write(self.style.SUCCESS('Successfully ran command makepayments'))
