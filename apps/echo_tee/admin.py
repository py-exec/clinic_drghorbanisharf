from django.contrib import admin
from .models import TEEEchoReport


@admin.register(TEEEchoReport)
class TEEEchoReportAdmin(admin.ModelAdmin):
    list_display = ("patient", "exam_datetime", "created_by", "created_at")
    search_fields = ("patient__first_name", "patient__last_name")
    list_filter = ("exam_datetime", "created_at")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("🔗 اطلاعات پایه", {
            "fields": ("patient", "prescription", "exam_datetime", "created_by")
        }),
        ("🧠 یافته‌های بالینی", {
            "fields": ("findings", "comments")
        }),
        ("📎 فایل پیوست", {
            "fields": ("echo_file",)
        }),
        ("🕓 متادیتا", {
            "fields": ("created_at",)
        }),
    )
