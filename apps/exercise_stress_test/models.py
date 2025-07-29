from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription  # نسخه پزشک

User = get_user_model()

class StressTestReport(models.Model):
    # عمومی
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="stress_tests", verbose_name="بیمار")
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name="stress_tests", verbose_name="نسخه")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")
    exam_datetime = models.DateTimeField("تاریخ انجام تست", default=timezone.now)

    # مشخصات تست
    stress_type = models.CharField(max_length=50, null=True, blank=True, verbose_name="نوع تست (ورزشی یا اکو)")
    protocol = models.CharField("پروتکل تست", max_length=100, null=True, blank=True)
    stress_duration = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="مدت تست (دقیقه)")
    test_duration = models.DurationField("مدت تست (فرمت زمان)", null=True, blank=True)
    stress_start_time = models.TimeField(null=True, blank=True, verbose_name="زمان شروع تست")
    stress_stop_reason = models.CharField(max_length=100, null=True, blank=True, verbose_name="علت توقف تست")
    stress_conditions = models.TextField(null=True, blank=True, verbose_name="شرایط حین تست")

    # شاخص‌های عملکرد قلب
    patient_age = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="سن بیمار")
    mets = models.FloatField(null=True, blank=True, verbose_name="METs")
    hr_rest = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="ضربان قلب در استراحت")
    hr_peak = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="ضربان قلب در اوج")
    hr_peak_metric = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="ضربان اوج (متریک)")
    max_hr = models.PositiveIntegerField("حداکثر HR", null=True, blank=True)
    target_hr = models.PositiveIntegerField("هدف HR", null=True, blank=True)

    sbp_rest = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="فشار سیستولیک در استراحت")
    sbp_peak = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="فشار سیستولیک در اوج")
    sbp_peak_metric = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="فشار اوج (متریک)")
    bp_during_test = models.CharField("فشار خون حین تست", max_length=50, null=True, blank=True)

    # ریکاوری
    recovery_duration = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="مدت ریکاوری")
    hr_recovery = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="ضربان قلب در ریکاوری")
    sbp_recovery = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="فشار سیستولیک در ریکاوری")
    recovery_st_change = models.CharField(max_length=50, null=True, blank=True, verbose_name="تغییرات ST در ریکاوری")
    recovery_symptoms = models.JSONField(null=True, blank=True, verbose_name="علائم در ریکاوری")
    recovery_monitoring = models.TextField(null=True, blank=True, verbose_name="پایش در ریکاوری")

    # پیش تست
    pretest_medications = models.CharField(max_length=100, null=True, blank=True, verbose_name="داروهای قبل از تست")
    baseline_ecg = models.CharField(max_length=100, null=True, blank=True, verbose_name="ECG پایه")
    pretest_sbp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="فشار سیستولیک قبل از تست")
    pretest_dbp = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="فشار دیاستولیک قبل از تست")
    pretest_contra = models.CharField(max_length=100, null=True, blank=True, verbose_name="موارد منع قبل از تست")

    # علائم بالینی و نتایج تست
    symptoms = models.JSONField(null=True, blank=True, verbose_name="علائم حین تست")
    stress_symptomatic = models.CharField(max_length=50, null=True, blank=True, verbose_name="تست علامت‌دار")
    borg_scale = models.CharField(max_length=10, null=True, blank=True, verbose_name="مقیاس بورگ")
    test_result = models.CharField("نتیجه تست", max_length=200, null=True, blank=True)

    # یافته‌های ECG
    arrhythmia_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="نوع آریتمی")
    ecg_leads = models.CharField(max_length=100, null=True, blank=True, verbose_name="لیدهای ECG")
    ecg_changes = models.TextField(null=True, blank=True, verbose_name="تغییرات ECG")

    # یافته‌های اکو
    wall_motion_abnormalities = models.BooleanField("اختلال حرکتی دیواره؟", default=False)
    ischemic_changes = models.BooleanField("تغییرات ایسکمیک؟", default=False)
    arrhythmia_occurred = models.BooleanField("آریتمی در حین تست؟", default=False)

    rwma_severity = models.CharField(max_length=50, null=True, blank=True, verbose_name="شدت RWMA")
    ef_rest = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="EF در استراحت")
    ef_post = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="EF پس از تست")
    mr_grade = models.CharField(max_length=50, null=True, blank=True, verbose_name="درجه MR")
    rwma_walls = models.TextField(null=True, blank=True, verbose_name="دیواره‌های درگیر RWMA")

    # فایل‌ها و مستندات
    stress_video = models.FileField(upload_to="stress_test/videos/", null=True, blank=True, verbose_name="ویدیوی تست")
    echo_file = models.FileField("فایل تست اکو", upload_to="echo/stress/", null=True, blank=True)
    image_saved = models.CharField(max_length=10, null=True, blank=True, verbose_name="تصاویر ذخیره شده")
    technical_issues = models.TextField(null=True, blank=True, verbose_name="مشکلات فنی")

    # نتیجه نهایی
    findings = models.TextField("یافته‌ها", blank=True, null=True)
    doctor_opinion = models.TextField("نظر پزشک", blank=True, null=True)
    recommendation = models.TextField("توصیه بعد از تست", blank=True, null=True)
    final_comment = models.TextField(null=True, blank=True, verbose_name="توضیح نهایی")
    final_diagnosis = models.CharField(max_length=50, null=True, blank=True, verbose_name="تشخیص نهایی")
    final_plan = models.CharField(max_length=200, null=True, blank=True, verbose_name="برنامه نهایی")

    class Meta:
        verbose_name = "تست ورزش / استرس اکو"
        verbose_name_plural = "گزارش‌های تست ورزش / استرس اکو"
        ordering = ["-created_at"]

    def __str__(self):
        return f"تست ورزش {self.patient} در {self.exam_datetime.strftime('%Y-%m-%d')}"