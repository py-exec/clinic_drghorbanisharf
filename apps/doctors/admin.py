from django.contrib import admin

from .models import SpecialtyCategory, Specialty, Doctor


@admin.register(SpecialtyCategory)
class SpecialtyCategoryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
    ordering = ("title",)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("title", "category")
    search_fields = ("title",)
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("title",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "medical_code", "specialty", "university", "is_active")
    list_filter = ("specialty", "university", "is_active")
    search_fields = ("user__first_name", "user__last_name", "medical_code")
    autocomplete_fields = ["user"]
    prepopulated_fields = {"slug": ("user",)}
    readonly_fields = ("created_at",)
    ordering = ("user__last_name",)
