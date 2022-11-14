from studios.models import Studio
from django.db.models.expressions import RawSQL


# Code heavily inspired by: https://stackoverflow.com/questions/19703975/django-sort-by-distance
def get_nearby_locs(latitude, longitude, max_dist=None):
    # Great circle distance formula
    gcd_formula = "6371 * acos(least(greatest(\
        cos(radians(%s)) * cos(radians(latitude)) \
        * cos(radians(longitude) - radians(%s)) + \
        sin(radians(%s)) * sin(radians(latitude)) \
        , -1), 1))"
    distance_raw_sql = RawSQL(
        gcd_formula,
        (latitude, longitude, latitude)
    )
    qs = Studio.objects.all().annotate(distance=distance_raw_sql).order_by('distance')
    if max_dist is not None:
        qs = qs.filter(distance__lt=max_dist)
    return qs


def convert_date_to_django_date(date_int):
    if date_int <= 5:
        return date_int + 2
    else:
        return 1
