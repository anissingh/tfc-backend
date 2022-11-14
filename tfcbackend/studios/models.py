from django.db import models
from django.core.exceptions import ValidationError
import math
from django.db.backends.signals import connection_created
from django.dispatch import receiver

# TODO: Remove blank and null = True from StudioImage image
# TODO: Maybe make coach its own model


# Validators
def validate_latitude(value):
    if -90.0 <= value <= 90.0:
        return value
    else:
        raise ValidationError('Latitude must be between -90 and 90 degrees.')


def validate_longitude(value):
    if -180.0 <= value <= 180.0:
        return value
    else:
        raise ValidationError('Longitude must be between -180 and 180 degrees.')


# Create your models here.
class Studio(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, validators=[validate_latitude])
    longitude = models.DecimalField(max_digits=11, decimal_places=8, validators=[validate_longitude])
    postal_code = models.CharField(max_length=6, unique=True)
    phone = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Studio'
        verbose_name_plural = 'Studios'


class StudioImage(models.Model):
    studio = models.ForeignKey(to=Studio, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', blank=True, null=True)

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

    def clean(self):
        super().clean()
        errors = {}
        if self.end_date <= self.start_date:
            errors['end_date'] = 'End date must be after the start date'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    def __str__(self):
        return f'{self.name}: from {self.start_date} until {self.end_date}'

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
    # TODO: Offer recurrence for bi-weekly, etc.
    # TODO: If I do this, would need to change datetime + timedelta(7) in admin.py
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
        if self.end_time and self.end_time <= self.start_time:
            errors['end_time'] = 'End time must be after start time.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    def __str__(self):
        return f'{self.day} - from {self.start_time} to {self.end_time}'

    class Meta:
        verbose_name = 'Class Time'
        verbose_name_plural = 'Class Times'


class ClassInstance(models.Model):
    # TODO: Do not allow cancelling a class if it has happened already? Reason is in history
    # TODO: we need to be able to remember that the user took this class
    # TODO: If all classes cancelled, delete class
    # TODO: Make name not editable (because of searching through studios for class name)
    cls = models.ForeignKey(to=Class, on_delete=models.CASCADE)
    date = models.DateField()
    start_date_and_time = models.DateTimeField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    enrolled = models.PositiveIntegerField(default=0)
    capacity = models.PositiveIntegerField()
    coach = models.CharField(max_length=200)

    def clean(self):
        super().clean()
        errors = {}
        if self.end_time <= self.start_time:
            errors['end_time'] = 'End time must be after start time.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save()

    def __str__(self):
        return f'{self.cls.name} on {self.date} - from {self.start_time} to {self.end_time}'

    class Meta:
        verbose_name = 'Class Instance'
        verbose_name_plural = 'Class Instances'


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
