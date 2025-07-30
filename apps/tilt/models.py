# apps / tilt / models.py
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from apps.reception.models import ReceptionService
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
User = get_user_model()


class TiltTestReport(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        verbose_name="بیمار"
    )

    # ==== وابستگی اصلی به خدمت پذیرش شده ====
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # ==== وابستگی‌های دیگر ====
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="tilt_tests", verbose_name="نسخه مرتبط")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="کاربر ثبت‌کننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")

    # ==== اطلاعات ارجاع ====
    referring_physician = models.CharField("پزشک ارجاع‌دهنده", max_length=100, blank=True, null=True)
    referral_reason = models.TextField("علت ارجاع", blank=True, null=True)

    # ==== علائم قبل از تست ====
    prior_symptoms = models.CharField("علائم قبلی", max_length=50, blank=True, null=True)
    last_event_time = models.DateTimeField("زمان آخرین حمله", blank=True, null=True)

    # ==== پاسخ تست تیلت ====
    had_syncope = models.CharField("آیا سنکوپ رخ داد؟", max_length=10, choices=[("yes", "بله"), ("no", "خیر")],
                                   blank=True, null=True)
    hr_during_syncope = models.PositiveIntegerField("HR حین سنکوپ", blank=True, null=True)
    bp_drop = models.CharField("فشار خون افت کرد؟", max_length=10, choices=[("yes", "بله"), ("no", "خیر")], blank=True,
                               null=True)
    symptom_onset_time = models.PositiveIntegerField("زمان بروز علائم (دقیقه)", blank=True, null=True)
    standing_symptoms = models.JSONField("علائم حین ایستادن", blank=True, null=True)

    # ==== فاز بازیابی ====
    recovery_time = models.PositiveIntegerField("زمان بازیابی (دقیقه)", blank=True, null=True)
    response_type = models.CharField("نوع پاسخ نهایی", max_length=50, blank=True, null=True)
    final_result = models.CharField("یافته نهایی پزشک", max_length=50, blank=True, null=True)
    tilt_upload = models.FileField("آپلود فایل تصویری یا گزارش", upload_to="tilt_tests/", blank=True, null=True)
    doctor_comment = models.TextField("توضیح پزشک", blank=True, null=True)

    # 👈 جدید: فیلد تاریخچه
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "گزارش تست تیلت"
        verbose_name_plural = "گزارش‌های تست تیلت"
        ordering = ["-created_at"]

    def __str__(self):
        patient_name = "بیمار نامشخص"
        if self.content_object and hasattr(self.content_object, "reception") and self.content_object.reception:
            patient_name = self.content_object.reception.patient.full_name()
        return f"تست تیلت برای {patient_name} - {self.created_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        if not self.referring_physician and self.prescription and self.prescription.doctor:
            self.referring_physician = self.prescription.doctor.user.get_full_name()

        self.full_clean()
        super().save(*args, **kwargs)

        # 📡 ارسال WebSocket
        try:
            if self.content_object and hasattr(self.content_object,
                                               "tariff") and self.content_object.tariff and self.content_object.tariff.service_type.assigned_role:
                role_code = self.content_object.tariff.service_type.assigned_role.code
                group_name = f"role_{role_code}"
                channel_layer = get_channel_layer()

                payload = {
                    "type": "reception_update",
                    "action": "report_created",
                    "service_id": self.object_id,
                    "service_type": self.content_object.tariff.service_type.code,
                    "report_id": self.pk,
                    "report_type": "tilt",
                    "created_at": self.created_at.isoformat(),
                    "created_by": self.created_by.get_full_name() if self.created_by else None,
                }

                async_to_sync(channel_layer.group_send)(group_name, payload)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"WebSocket ارسال نشد برای گزارش تیلت {self.pk}: {e}")

    def clean(self):
        """
        اعتبارسنجی‌های سطح مدل.
        """
        super().clean()
        if self.had_syncope == 'yes' and self.hr_during_syncope is None:
            raise ValidationError({
                'hr_during_syncope': 'در صورت وقوع سنکوپ، ثبت ضربان قلب حین آن الزامی است.'
            })

    def get_absolute_url(self):
        return reverse('tilt:tilt_detail', kwargs={'pk': self.pk})

    @property
    def reception_service(self):
        if isinstance(self.content_object, ReceptionService):
            return self.content_object
        return None
