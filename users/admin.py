from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser


class MyUserAdmin(UserAdmin):
    model = MyUser
    list_display = (
        "username",
        "email",
        "refresh_token_expires_at",
        "is_active",
        "is_staff",
    )
    list_editable = (
        "refresh_token_expires_at",
        "is_active",
        "is_staff",
    )
    fieldsets = UserAdmin.fieldsets + (
        ("Extra Fields", {"fields": ("refresh_token", "refresh_token_expires_at")}),
    )


admin.site.register(MyUser, MyUserAdmin)
