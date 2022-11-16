from subscriptions.models import UserSubscription, Payment
from accounts.models import User
from datetime import datetime
from datetime import timedelta
from django.utils.timezone import now, localdate, localtime, make_aware


def make_payment(user_subscription):
    # Make payment
    user = user_subscription.user
    card_used = user_subscription.payment_card
    amount = user_subscription.amount
    date_and_time = get_curr_datetime()
    payment = Payment(user=user, card_used=card_used, amount=amount,
                      date_and_time=date_and_time)
    payment.save()

    # Update user's next payment due date and amount if subscription plan still exists
    subscription_plan = user_subscription.subscription_plan
    if subscription_plan:
        curr_date = localdate()
        user_subscription.next_payment_day = calculate_next_payment_day(curr_date, subscription_plan)
        user_subscription.amount = subscription_plan.amount
        user_subscription.save()
    else:
        # Delete user subscription
        user_subscription.delete()

        # Un-enroll user in any classes they are enrolled in after their billing period ends
        # User IS ALLOWED to be in classes on the day of cancellation to prevent users being mad
        # about paying at 6pm so they should be able to attend classes until 6pm on cancel date
        all_enrolled_classes = user.enrolled_classes.all()
        enrolled_after_billing = all_enrolled_classes.filter(date__gt=localdate())
        for class_instance in enrolled_after_billing:
            user.enrolled_classes.remove(class_instance)
            class_instance.enrolled -= 1
            class_instance.save()


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
