from django.contrib import admin
from .models import TTEEchoReport



@admin.register(TTEEchoReport)
class TTEEchoReportAdmin(admin.ModelAdmin):
    list_display = (
        "patient", "exam_datetime", "ef", "tapse", "spap",
        "image_quality", "created_by", "created_at"
    )
    list_filter = (
        "image_quality", "pericardial_effusion", "created_at"
    )
    search_fields = (
        "patient__first_name", "patient__last_name", "ef", "spap", "doctor_opinion", "recommendation"
    )
    readonly_fields = ("created_at", "created_by")

    fieldsets = (
        ("🩺 اطلاعات پایه", {
            "fields": ("patient", "prescription", "exam_datetime")
        }),
        ("📊 عملکرد بطن چپ", {
            "fields": ("ef", "lv_dysfunction", "lvedd", "lvesd", "gls", "image_type")
        }),
        ("💓 عملکرد RV و فشار ریوی", {
            "fields": ("tapse", "spap", "ivc_status")
        }),
        ("🚪 وضعیت دریچه‌ها", {
            "fields": (
                ("mitral_type", "mitral_severity", "mitral_features"),
                ("aortic_type", "aortic_severity", "aortic_features"),
                ("tricuspid_type", "tricuspid_severity"),
                ("pulmonary_type", "pulmonary_severity")
            )
        }),
        ("🧱 ساختار غیرطبیعی و مایعات", {
            "fields": ("pericardial_effusion", "pleural_effusion", "mass_or_clot", "aneurysm")
        }),
        ("🖼️ کیفیت تصویر", {
            "fields": ("image_quality", "image_limitation_reason", "probe_type", "ecg_sync")
        }),
        ("👨‍🔧 نظر تکنسین", {
            "fields": ("technician_name", "technician_note", "patient_cooperation", "all_views_taken")
        }),
        ("🩻 گزارش نهایی پزشک", {
            "fields": ("reporting_physician", "report_date", "need_advanced_echo", "reason_advanced_echo", "final_report")
        }),
        ("📎 فایل‌ها", {
            "fields": ("upload_file",)
        }),
        ("🕓 متادیتا", {
            "fields": ("created_by", "created_at")
        })
    )

