from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver
from studios.models import Studio, StudioImage, StudioAmenities, Class, Keyword, ClassInstance
from studios.models import ClassTime
import datetime
from django.utils.timezone import make_aware, localdate, localtime
from studios.utils import get_next_weekday, get_curr_datetime


# Register your models here.
class StudioImageInline(admin.TabularInline):
    model = StudioImage
    fields = ['image']


class StudioAmenitiesInline(admin.TabularInline):
    model = StudioAmenities
    fields = ['type', 'quantity']


class StudioAdmin(admin.ModelAdmin):
    fields = ['name', 'address', 'latitude', 'longitude', 'postal_code', 'phone']
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
    readonly_fields = []
    fields = ['name', 'description', 'studio', 'coach', 'capacity', 'start_date', 'end_date']
    list_display = ['name', 'studio', 'coach', 'start_date', 'end_date', 'capacity',
                    'active']
    inlines = [ClassTimeInline, KeywordInline]

    @admin.display(boolean=True, description='All Future Classes Active')
    def active(self, obj):
        return not obj.cancel_all_future

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.readonly_fields + ['cancel_all_future']
        else:
            return self.readonly_fields + ['start_date']

    def get_fields(self, request, obj=None):
        if obj:
            return self.fields + ['cancel_all_future']
        else:
            return self.fields

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.end_date < localdate():
            return False
        elif obj and not obj.studio:
            return False
        else:
            return super().has_change_permission(request, obj)


class ClassInstanceAdmin(admin.ModelAdmin):
    readonly_fields = ['cls', 'enrolled']
    list_display = ['cls', 'date', 'start_time', 'end_time', 'enrolled', 'capacity', 'coach',
                    'active']
    fields = ['cls', 'date', 'start_time', 'end_time', 'enrolled', 'capacity', 'coach',
              'cancelled']

    @admin.display(ordering='cls__name', description='Class Name')
    def get_author(self, obj):
        return obj.cls.name

    @admin.display(boolean=True)
    def active(self, obj):
        return not obj.cancelled

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.start_date_and_time < get_curr_datetime():
            return False
        elif obj and obj.cls and not obj.cls.studio:
            return False
        else:
            return super().has_change_permission(request, obj)


@receiver(post_save, sender=ClassTime)
def generate_class_instances(sender, instance, created, **kwargs):
    ct = instance
    obj = instance.cls
    if created:
        _generate_class_instances_helper(obj, ct)


def _generate_class_instances_helper(obj, ct):
    if obj.start_date.weekday() == ct.day and obj.start_date == localdate() and \
            ct.start_time < localtime().time():
        curr_date = localdate() + datetime.timedelta(weeks=1)
    else:
        curr_date = get_next_weekday(obj.start_date, ct.day)
    while curr_date < obj.end_date:
        start_date_and_time = make_aware(datetime.datetime.combine(curr_date, ct.start_time))
        ci = ClassInstance(cls=obj, date=curr_date, start_time=ct.start_time,
                           start_date_and_time=start_date_and_time, end_time=ct.end_time,
                           capacity=obj.capacity, coach=obj.coach)
        ci.save()
        curr_date = curr_date + datetime.timedelta(7)


admin.site.register(Studio, StudioAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(ClassInstance, ClassInstanceAdmin)
