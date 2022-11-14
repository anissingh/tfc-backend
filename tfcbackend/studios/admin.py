from django.contrib import admin
from studios.models import Studio, StudioImage, StudioAmenities, Class, Keyword, ClassInstance
from studios.models import ClassTime
from django.utils.timezone import make_aware
import datetime


# Register your models here.
class StudioImageInline(admin.TabularInline):
    model = StudioImage
    fields = ['image']


class StudioAmenitiesInline(admin.TabularInline):
    model = StudioAmenities
    fields = ['type', 'quantity']


class StudioAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    fields = ['id', 'name', 'address', 'latitude', 'longitude', 'postal_code', 'phone']
    list_display = ['name', 'id', 'address', 'latitude', 'longitude', 'postal_code', 'phone']
    inlines = [StudioImageInline, StudioAmenitiesInline]


class KeywordInline(admin.TabularInline):
    model = Keyword
    readonly_fields = ['cls']
    fields = ['word', 'cls']


class ClassTimeInline(admin.TabularInline):
    model = ClassTime
    readonly_fields = ['cls']
    fields = ['cls', 'day', 'start_time', 'end_time']


class ClassAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'studio', 'coach', 'capacity', 'start_date', 'end_date']
    list_display = ['name', 'studio', 'coach', 'start_date', 'end_date', 'capacity']
    inlines = [ClassTimeInline, KeywordInline]

    def save_model(self, request, obj, form, change):
        # TODO: Don't create new classes if no ClassTime or Class attributes were edited
        # TODO: Remove old classes and create new ones when ClassTime objects are updated
        super().save_model(request, obj, form, change)
        # obj.save()
        if change:
            self._generate_class_instances(obj)

    def _generate_class_instances(self, obj):
        class_times = ClassTime.objects.filter(cls=obj)

        for ct in class_times:
            curr_date = self._get_next_weekday(obj.start_date, ct.day)
            while curr_date < obj.end_date:
                start_date_and_time = make_aware(datetime.datetime.combine(curr_date, ct.start_time))
                ci = ClassInstance(cls=obj, date=curr_date, start_time=ct.start_time,
                                   start_date_and_time=start_date_and_time, end_time=ct.end_time,
                                   capacity=obj.capacity, coach=obj.coach)
                ci.save()
                curr_date = curr_date + datetime.timedelta(7)

    def _get_next_weekday(self, date, weekday):
        days_ahead = weekday - date.weekday()
        if days_ahead < 0:  # Target day already happened this week
            days_ahead += 7
        return date + datetime.timedelta(days_ahead)


admin.site.register(Studio, StudioAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(ClassInstance)
