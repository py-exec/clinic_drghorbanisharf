from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, AccessPermission


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("username", "first_name", "last_name", "role", "is_active", "is_verified")
    list_filter = ("is_active", "role", "is_verified")
    search_fields = ("username", "first_name", "last_name", "phone_number", "national_code")
    autocomplete_fields = ["role"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "nickname", "phone_number", "national_code", "email", "profile_image")}),
        ("دسترسی‌ها", {"fields": ("role", "is_active", "is_verified", "phone_verified", "email_verified", "is_superuser", "groups", "user_permissions")}),
        ("متا", {"fields": ("last_login", "date_joined", "created_by", "last_seen", "ip_address")}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    filter_horizontal = ("permissions",)


@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
