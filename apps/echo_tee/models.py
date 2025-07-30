# apps/echo_tee/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.contrib.contenttypes.fields import GenericForeignKey # NEW: Import GenericForeignKey
from django.contrib.contenttypes.models import ContentType # NEW: Import ContentType

User = get_user_model()

class TEEEchoReport(models.Model):
    """
    مدل گزارش اکو از راه مری (TEE).
    این مدل به عنوان رکورد تخصصی یک خدمت ReceptionService عمل می‌کند.
    """
    # NEW: GenericForeignKey for linking to ReceptionService
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True) # Temporarily nullable for migration
    object_id = models.PositiveIntegerField(null=True, blank=True) # Temporarily nullable for migration
    reception_service = GenericForeignKey('content_type', 'object_id')

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

    echo_file = models.FileField("فایل پیوست", upload_to="echo/tee/", null=True, blank=True) # Renamed to align with a more generic name if needed, but current name is echo_file

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "اکو مری (TEE)"
        verbose_name_plural = "اکوهای مری"
        ordering = ['-created_at']

    def __str__(self):
        return f"TEE برای {self.patient.first_name} {self.patient.last_name} در {self.exam_datetime.strftime('%Y-%m-%d')}"

    # NEW: Override save to update ReceptionService status and trigger signals
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.full_clean() # Run full validation before saving
        super().save(*args, **kwargs)

        # After saving the TEE report, update the status of the related ReceptionService
        if self.reception_service:
            from apps.reception.status_service import change_service_status # Lazy import
            # TEE is a single-stage report, so completing it means service is completed
            change_service_status(
                self.reception_service, 
                'completed', # Set service status to 'completed'
                user=self.created_by, # Use created_by for status change if available
                note=f"گزارش اکو مری (TEE) ثبت/به‌روزرسانی شد."
            )