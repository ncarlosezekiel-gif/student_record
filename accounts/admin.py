from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class SRMSUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("role", "phone")}),
    )
    fieldsets = UserAdmin.fieldsets + (("SRMS profile", {"fields": ("role", "phone")}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
