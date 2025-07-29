from django.contrib import admin
from .models import StressTestReport


@admin.register(StressTestReport)
class StressTestAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "prescription",
        "created_at",
        "stress_type",
        "final_diagnosis",
        "final_plan",
        "created_by",
    )
    list_filter = (
        "stress_type",
        "final_diagnosis",
        "created_at",
    )
    search_fields = (
        "patient__national_code",
        "patient__first_name",
        "patient__last_name",
        "final_comment",
    )
    readonly_fields = ("created_at",)

    fieldsets = (
        ("مشخصات پایه", {
            "fields": ("patient", "prescription", "created_by", "created_at")
        }),
        ("شاخص‌های عملکردی قلبی", {
            "fields": (
                "patient_age", "hr_peak_metric", "mets",
                "sbp_peak_metric"
            )
        }),
        ("فاز بازیابی", {
            "fields": (
                "recovery_duration", "hr_recovery", "sbp_recovery",
                "recovery_st_change", "recovery_symptoms", "recovery_monitoring"
            )
        }),
        ("اطلاعات پیش‌تست", {
            "fields": (
                "pretest_medications", "baseline_ecg",
                "pretest_sbp", "pretest_dbp", "pretest_contra"
            )
        }),
        ("اطلاعات تست", {
            "fields": (
                "stress_type", "stress_start_time", "stress_duration",
                "stress_stop_reason", "stress_conditions"
            )
        }),
        ("علائم بالینی", {
            "fields": (
                "symptoms", "hr_rest", "hr_peak", "sbp_rest", "sbp_peak",
                "stress_symptomatic", "borg_scale"
            )
        }),
        ("یافته‌های ECG", {
            "fields": (
                "arrhythmia_type", "ecg_leads", "ecg_changes"
            )
        }),
        ("یافته‌های اکو", {
            "fields": (
                "rwma_severity", "ef_rest", "ef_post", "mr_grade", "rwma_walls"
            )
        }),
        ("مستندات", {
            "fields": (
                "stress_video", "image_saved", "technical_issues"
            )
        }),
        ("تحلیل نهایی", {
            "fields": (
                "final_comment", "final_diagnosis", "final_plan"
            )
        }),
    )