from django.contrib import admin
from subscriptions.models import SubscriptionPlan


# Register your models here.
class SubscriptionPlanAdmin(admin.ModelAdmin):
    fields = ['name', 'amount', 'frequency', 'description']
    list_display = ['name', 'amount', 'frequency']


admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
