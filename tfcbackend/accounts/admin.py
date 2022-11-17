from django.contrib import admin
from accounts.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'id', 'phone']
    fields = ['id', 'email', 'phone', 'avatar']
    readonly_fields = ['id', 'email', 'phone', 'avatar']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Register your models here.
admin.site.register(User, UserAdmin)
