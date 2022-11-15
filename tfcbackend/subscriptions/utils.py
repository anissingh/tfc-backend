from subscriptions.models import UserSubscription, Payment
from accounts.models import User
from datetime import datetime
from datetime import timedelta
from django.utils.timezone import now, localdate, localtime, make_aware


def make_payment(user_subscription):
    # Make payment
    user = user_subscription.user
    card_used = user_subscription.payment_card
    subscription_plan = user_subscription.subscription_plan
    date_and_time = get_curr_datetime()
    payment = Payment(user=user, card_used=card_used, subscription_plan=subscription_plan,
                      date_and_time=date_and_time)
    payment.save()

    # Update user's next payment due date
    curr_date = localdate()
    user_subscription.next_payment_day = calculate_next_payment_day(curr_date, subscription_plan)
    user_subscription.save()


def get_curr_datetime():
    curr_date = localdate()
    curr_time = localtime().time()
    return make_aware(datetime.combine(curr_date, curr_time))


def calculate_next_payment_day(date, subscription_plan):
    if subscription_plan.frequency == 0:
        # Weekly
        date += timedelta(weeks=1)
    elif subscription_plan.frequency == 1:
        # Bi-Weekly
        date += timedelta(weeks=2)
    elif subscription_plan.frequency == 2:
        # Monthly
        date += timedelta(weeks=4)
    elif subscription_plan.frequency == 3:
        # Every 3 months
        date += timedelta(weeks=12)
    elif subscription_plan.frequency == 4:
        # Every 6 months
        date += timedelta(weeks=24)
    else:
        # Every year
        date += timedelta(weeks=52)

    return date
