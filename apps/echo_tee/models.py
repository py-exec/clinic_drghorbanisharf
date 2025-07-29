from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription  # نسخه پزشک

User = get_user_model()

class TEEEchoReport(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE,
        related_name="tee_echos", verbose_name="بیمار"
    )

    prescription = models.ForeignKey(
        Prescription, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="tee_echos", verbose_name="نسخه مربوطه"
    )

    exam_datetime = models.DateTimeField("تاریخ انجام", default=timezone.now)

    sedation_used = models.CharField("نوع آرام‌بخش", max_length=100, null=True, blank=True)
    patient_cooperation = models.CharField(
        "میزان همکاری بیمار", max_length=50,
        choices=[
            ("good", "خوب"), ("moderate", "متوسط"), ("poor", "ضعیف")
        ],
        null=True, blank=True
    )
    visualization_quality = models.CharField(
        "کیفیت تصاویر", max_length=50,
        choices=[
            ("excellent", "عالی"), ("good", "خوب"), ("acceptable", "قابل قبول"), ("poor", "ضعیف")
        ],
        null=True, blank=True
    )

    la_appendage_status = models.TextField("وضعیت LAA", null=True, blank=True)
    interatrial_septum = models.TextField("سپتوم بین دهلیزی", null=True, blank=True)
    valvular_findings = models.TextField("مشاهدات مربوط به دریچه‌ها", null=True, blank=True)
    presence_of_clot = models.BooleanField("وجود لخته؟", default=False)
    pericardial_effusion = models.BooleanField("افیوژن پریکارد؟", default=False)

    findings = models.TextField("یافته‌ها", blank=True, null=True)
    doctor_opinion = models.TextField("نظر پزشک", blank=True, null=True)
    recommendation = models.TextField("توصیه", blank=True, null=True)

    echo_file = models.FileField("فایل پیوست", upload_to="echo/tee/", null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "اکو مری (TEE)"
        verbose_name_plural = "اکوهای مری"
        ordering = ['-created_at']

    def __str__(self):
        return f"TEE برای {self.patient.first_name} {self.patient.last_name} در {self.exam_datetime.strftime('%Y-%m-%d')}"