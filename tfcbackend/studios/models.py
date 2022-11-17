from django.db import models
from django.core.exceptions import ValidationError
import math
from django.db.backends.signals import connection_created
from django.dispatch import receiver
from studios.utils import get_next_weekday, get_curr_datetime
from django.utils.timezone import localdate, make_aware, localtime
import datetime


# Create your models here.
class Studio(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    postal_code = models.CharField(max_length=6, unique=True)
    phone = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        errors = {}
        if self.latitude and (self.latitude < -90.0 or self.latitude > 90.0):
            errors['latitude'] = 'Latitude must be between -90 and 90 degrees.'
        if self.longitude and (self.longitude < -180.0 or self.longitude > 180.0):
            errors['longitude'] = 'Longitude must be between -180 and 180 degrees.'
        if self.phone and (not self.phone.isnumeric() or len(self.phone) != 10):
            errors['phone'] = 'Invalid phone number.'
        if self.postal_code and not validate_postal_code(self.postal_code):
            errors['postal_code'] = 'Invalid postal code.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    class Meta:
        verbose_name = 'Studio'
        verbose_name_plural = 'Studios'


class StudioImage(models.Model):
    studio = models.ForeignKey(to=Studio, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='studio-images/', default='studio-images/default.jpg')

    class Meta:
        verbose_name = 'Studio Image'
        verbose_name_plural = 'Studio Images'


class StudioAmenities(models.Model):
    studio = models.ForeignKey(to=Studio, on_delete=models.CASCADE)
    type = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.type}: ({self.quantity})'

    class Meta:
        verbose_name = 'Studio Amenities'
        verbose_name_plural = 'Studio Amenities'


class Class(models.Model):
    studio = models.ForeignKey(to=Studio, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    coach = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    cancel_all_future = models.BooleanField(default=False, verbose_name='Cancel all Future Classes')

    def clean(self):
        super().clean()
        errors = {}
        old = type(self).objects.get(pk=self.pk) if self.pk else None
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            errors['end_date'] = 'End date must be after the start date'
        if self.start_date and self.start_date < localdate():
            errors['start_date'] = 'Start date must be at least current date'
        if old and self.capacity < old.capacity:
            errors['capacity'] = 'Cannot reduce capacity of class'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        old = type(self).objects.get(pk=self.pk) if self.pk else None
        super().save()
        if old:
            if not old.cancel_all_future and self.cancel_all_future:
                cancel_all_future_classes(self)
            if old.cancel_all_future and not self.cancel_all_future:
                reactivate_all_future_classes(self)
            if old.end_date < self.end_date:
                # add classes between old end date and new end date
                add_classes_in_between(self, old.end_date, self.end_date)
            if self.end_date < old.end_date:
                # remove classes between new end date and old end date
                cancel_classes_in_between(self, self.end_date)
            if self.coach != old.coach:
                # update all future coaches (including cancelled classes)
                # note: do not update any coaches of classes with custom set coaches
                update_coaches(self, old.coach)
            if self.capacity != old.capacity:
                update_capacity(self, old.capacity)

    def delete(self, using=None, keep_parents=False):
        cancel_all_future_classes(self)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'


class Keyword(models.Model):
    cls = models.ForeignKey(to=Class, on_delete=models.CASCADE)
    word = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Keyword'
        verbose_name_plural = 'Keywords'


class ClassTime(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    cls = models.ForeignKey(to=Class, on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        super().clean()
        errors = {}
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            errors['end_time'] = 'End time must be after start time.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        old = type(self).objects.get(pk=self.pk) if self.pk else None
        super().save()
        if old:
            if old.start_time != self.start_time or old.end_time != self.end_time or old.day != self.day:
                update_class_instances_upon_time_change(self, old)

    def __str__(self):
        return f'{self.day} - from {self.start_time} to {self.end_time}'

    class Meta:
        verbose_name = 'Class Time'
        verbose_name_plural = 'Class Times'


class ClassInstance(models.Model):
    cls = models.ForeignKey(to=Class, on_delete=models.CASCADE, verbose_name='Class Name')
    date = models.DateField()
    start_date_and_time = models.DateTimeField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    enrolled = models.PositiveIntegerField(default=0)
    capacity = models.PositiveIntegerField()
    coach = models.CharField(max_length=200)
    cancelled = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        errors = {}
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            errors['end_time'] = 'End time must be after start time.'
        if self.enrolled and self.capacity and self.enrolled > self.capacity:
            errors['capacity'] = 'Too little capacity for users enrolled in this class.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    def cancel(self):
        self.cancelled = True
        self.save()

    def activate(self):
        self.cancelled = False
        self.save()

    def update_coach(self, coach_name):
        self.coach = coach_name
        self.save()

    def update_capacity(self, capacity):
        self.capacity = capacity
        self.save()

    def delete(self, using=None, keep_parents=False):
        self.cancel()

    def __str__(self):
        return f'{self.cls.name} on {self.date} - from {self.start_time} to {self.end_time}'

    class Meta:
        verbose_name = 'Class Instance'
        verbose_name_plural = 'Class Instances'


def update_class_instances_upon_time_change(ct, old_ct):
    # Get old class instances
    start_time = old_ct.start_time
    end_time = old_ct.end_time
    filter_date = localdate()

    old_cis = ClassInstance.objects.filter(start_time=start_time, end_time=end_time,
                                           date__gte=filter_date)
    for ci in old_cis:
        ci.start_time = ct.start_time
        ci.end_time = ct.end_time
        new_date = get_next_weekday(ci.date, ct.day)
        if ct.cls.end_date < new_date:
            ci.cancel()
        else:
            new_dt = make_aware(datetime.datetime.combine(new_date, ct.start_time))
            ci.date = new_date
            ci.start_date_and_time = new_dt
            ci.save()


def cancel_all_future_classes(cls):
    curr_dt = get_curr_datetime()
    ci_to_cancel = ClassInstance.objects.filter(cls=cls, start_date_and_time__gte=curr_dt)
    for ci in ci_to_cancel:
        ci.cancel()


def reactivate_all_future_classes(cls):
    curr_dt = get_curr_datetime()
    ci_to_active = ClassInstance.objects.filter(cls=cls, start_date_and_time__gte=curr_dt)
    for ci in ci_to_active:
        ci.activate()


def cancel_classes_in_between(cls, begin_date):
    ci_to_cancel = ClassInstance.objects.filter(cls=cls, date__gte=begin_date)
    for ci in ci_to_cancel:
        ci.cancel()


def add_classes_in_between(cls, begin_date, end_date):
    # Get classes that can be re-activated
    ci_to_active = ClassInstance.objects.filter(cls=cls, date__gte=localdate())

    class_times = ClassTime.objects.filter(cls=cls)
    for ct in class_times:
        curr_date = get_next_weekday(begin_date, ct.day)
        while curr_date < end_date:
            if ci_to_active.filter(date=curr_date).exists():
                ci = ci_to_active.get(date=curr_date)
                ci.activate()
            else:
                start_date_and_time = make_aware(datetime.datetime.combine(curr_date, ct.start_time))
                ci = ClassInstance(cls=cls, date=curr_date, start_time=ct.start_time,
                                   start_date_and_time=start_date_and_time, end_time=ct.end_time,
                                   capacity=cls.capacity, coach=cls.coach)
                ci.save()
            curr_date = curr_date + datetime.timedelta(7)


def update_coaches(cls, old_coach):
    curr_dt = get_curr_datetime()
    ci_to_update = ClassInstance.objects.filter(cls=cls, start_date_and_time__gte=curr_dt,
                                                coach=old_coach)
    for ci in ci_to_update:
        ci.update_coach(cls.coach)


def update_capacity(cls, old_capacity):
    curr_dt = get_curr_datetime()
    ci_to_update = ClassInstance.objects.filter(cls=cls, start_date_and_time__gte=curr_dt,
                                                capacity=old_capacity)
    for ci in ci_to_update:
        ci.update_capacity(cls.capacity)


def validate_postal_code(postal_code):
    if len(postal_code) != 6:
        return False
    if not postal_code.isalnum():
        return False

    digits = 0
    letters = 0
    for c in postal_code:
        if c.isdigit():
            digits += 1
        elif c.isupper():
            letters += 1
        else:
            return False

    if digits != 3 or letters != 3:
        return False

    return True


# Code from: https://stackoverflow.com/questions/19703975/django-sort-by-distance
@receiver(connection_created)
def extend_sqlite(connection=None, **kwargs):
    if connection.vendor == "sqlite":
        # sqlite doesn't natively support math functions, so add them
        cf = connection.connection.create_function
        cf('acos', 1, math.acos)
        cf('cos', 1, math.cos)
        cf('radians', 1, math.radians)
        cf('sin', 1, math.sin)
        cf('least', 2, min)
        cf('greatest', 2, max)
