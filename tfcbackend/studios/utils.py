import datetime
from django.utils.timezone import localdate, make_aware, localtime


def get_next_weekday(date, weekday):
    days_ahead = weekday - date.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return date + datetime.timedelta(days_ahead)


def get_curr_datetime():
    curr_date = localdate()
    curr_time = localtime().time()
    return make_aware(datetime.datetime.combine(curr_date, curr_time))
