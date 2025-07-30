# apps/ecg/models.py

import os
import hashlib
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey  # Already imported
from django.contrib.contenttypes.models import ContentType  # Already imported
from apps.patient.models import Patient  # Already imported
from apps.prescriptions.models import Prescription  # Already imported
from apps.patient.models import PatientFile  # Already imported

User = get_user_model()


class ECGRecord(models.Model):
    # ==== وابستگی‌ها ====
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="ecg_records",
        verbose_name="بیمار"
    )
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ecg_records",
        verbose_name="نسخه مربوطه"
    )
    # NEW: Changed created_by to allow null for existing records if it wasn't already
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow blank for forms too
        verbose_name="کاربر ثبت‌کننده"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")
    is_approved_by_doctor = models.BooleanField(default=False, verbose_name="تأیید پزشک")

    # ==== اطلاعات ثبت نوار ====
    ecg_type = models.CharField(
        max_length=20,
        choices=[("12lead", "۱۲ لید"), ("rhythm", "ریتم"), ("stress", "استرس")],
        verbose_name="نوع نوار"
    )
    patient_position = models.CharField(max_length=50, blank=True, verbose_name="وضعیت بیمار هنگام ثبت")
    room_temp = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="دمای اتاق")
    ecg_location = models.CharField(max_length=100, blank=True, verbose_name="محل انجام نوار")
    ecg_quality = models.CharField(
        max_length=20,
        choices=[("good", "خوب"), ("noisy", "نویزدار"), ("incomplete", "ناقص")],
        blank=True,
        verbose_name="کیفیت نوار"
    )
    tech_issue = models.BooleanField(default=False, verbose_name="آیا مشکل تکنیکی وجود داشت؟")
    issue_desc = models.TextField(blank=True, null=True, verbose_name="توضیح مشکل (در صورت وجود)")
    device_serial = models.CharField(max_length=100, blank=True, verbose_name="شماره سریال دستگاه ECG")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="زمان شروع")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")

    # ==== تحلیل اولیه ECG ====
    hr = models.PositiveIntegerField(null=True, blank=True, verbose_name="HR (ضربان)")
    rhythm = models.CharField(max_length=100, blank=True, verbose_name="ریتم غالب")
    axis = models.CharField(max_length=50, blank=True, verbose_name="محور قلب (Axis)")
    qrs = models.CharField(max_length=50, blank=True, verbose_name="QRS")
    qtc = models.CharField(max_length=50, blank=True, verbose_name="QTc")
    p_wave = models.CharField(max_length=50, blank=True, verbose_name="P موج")
    st_t = models.CharField(max_length=100, blank=True, verbose_name="ST-T تغییرات")
    q_wave = models.BooleanField(default=False, verbose_name="Q موج پاتولوژیک؟")
    u_wave = models.BooleanField(default=False, verbose_name="U موج مشاهده شد؟")
    tech_opinion = models.TextField(blank=True, verbose_name="توضیح تکنسین")

    # ==== فایل و نهایی‌سازی ====
    ecg_file = models.FileField(upload_to="ecg_files/", null=True, blank=True, verbose_name="فایل نوار قلب")
    ecg_repeat = models.BooleanField(default=False, verbose_name="نیاز به تکرار نوار؟")
    repeat_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="دلیل تکرار")

    # NEW: Changed tech_signature and doctor_signature to ForeignKey to User
    tech_signature = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ecg_tech_signatures",
        verbose_name="تکنسین ثبت‌کننده (امضا)"  # Renamed for clarity to avoid confusion with created_by
    )
    doctor_signature = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ecg_doctor_signatures",
        verbose_name="پزشک تأییدکننده (امضا)"
    )
    ai_result = models.TextField(blank=True, verbose_name="نتیجه تحلیل سیستم هوشمند")

    # NEW: Renamed 'service' to 'reception_service' for consistency, and explicitly define GFK fields nullable for migration
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    reception_service = GenericForeignKey("content_type", "object_id")  # Changed name from 'service'

    class Meta:
        verbose_name = "نوار قلب (ECG)"
        verbose_name_plural = "نوارهای قلب"
        ordering = ['-created_at']

    def __str__(self):
        return f"ECG برای {self.patient} - {self.created_at.strftime('%Y-%m-%d')}"

    def short_label(self):
        return f"{self.ecg_type} | {self.created_at.strftime('%Y-%m-%d')} | {self.patient.national_code if self.patient else 'N/A'}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if this is a new instance

        # Saving unique name for ECG file
        if self.ecg_file and not self.ecg_file.name.startswith("ecg_"):
            ext = self.ecg_file.name.split('.')[-1]
            raw = f"{self.patient.id if self.patient else 'unknown'}-{timezone.now().isoformat()}".encode('utf-8')
            hash_id = hashlib.sha256(raw).hexdigest()[:10]
            timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
            filename = f"ecg_{hash_id}_{timestamp}.{ext}"
            self.ecg_file.name = os.path.join("ecg_files", filename)

        self.full_clean()  # Run full validation before saving
        super().save(*args, **kwargs)

        # Linking file to patient
        if self.ecg_file and not PatientFile.objects.filter(related_ecg=self).exists():
            PatientFile.objects.create(
                patient=self.patient,
                file=self.ecg_file,
                title="نوار قلب ثبت‌شده",
                category="ecg",
                related_ecg=self,
                uploaded_by=self.created_by  # Ensure created_by is set before save
            )

        # NEW: Update the status of the related ReceptionService
        if self.reception_service:
            from apps.reception.status_service import change_service_status  # Lazy import
            # ECG is a single-stage report, so creating/updating it means service is completed
            change_service_status(
                self.reception_service,
                'completed',  # Set service status to 'completed'
                user=self.created_by,  # Use created_by for status change if available
                note=f"گزارش نوار قلب (ECG) ثبت/به‌روزرسانی شد. نوع: {self.ecg_type}, کیفیت: {self.ecg_quality}"
            )