from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords

User = settings.AUTH_USER_MODEL


class HolterHRInstallation(models.Model):
    """
    مرحله اول: نصب دستگاه هلتر ضربان (HR)
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reception_service = GenericForeignKey('content_type', 'object_id')

    patient = models.ForeignKey(
        "patient.Patient",
        on_delete=models.PROTECT,
        related_name="hr_holter_installations",
        verbose_name="بیمار"
    )

    tracking_code = models.CharField(max_length=30, unique=True, editable=False, verbose_name="کد پیگیری")

    device = models.ForeignKey(
        "inventory.Item",
        on_delete=models.PROTECT,
        verbose_name="دستگاه هلتر"
    )
    install_datetime = models.DateTimeField(verbose_name="زمان و تاریخ نصب")
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hr_holter_installations_done",
        verbose_name="تکنسین نصب"
    )
    patient_education_given = models.BooleanField(default=False, verbose_name="آموزش به بیمار داده شده؟")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌های زمان نصب")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_hr_holter_installations",
        verbose_name="کاربر ثبت‌کننده"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "نصب هلتر ضربان"
        verbose_name_plural = "نصب‌های هلتر ضربان"
        ordering = ['-install_datetime']
        indexes = [
            models.Index(fields=["install_datetime"]),
            models.Index(fields=["tracking_code"]),
            models.Index(fields=["patient"]),
        ]

    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', lambda: '---')()
        return f"نصب هلتر ضربان برای {patient_name} در تاریخ {self.install_datetime.strftime('%Y-%m-%d')}"

    def clean(self):
        super().clean()
        if self.install_datetime > timezone.now():
            raise ValidationError("تاریخ نصب نمی‌تواند در آینده باشد.")
        if self.reception_service and self.reception_service.reception.patient != self.patient:
            raise ValidationError("بیمار انتخاب‌شده با بیمار ثبت‌شده در پذیرش مطابقت ندارد.")
        if self.pk is None and self.__class__.objects.filter(content_type=self.content_type,
                                                             object_id=self.object_id).exists():
            raise ValidationError("برای این خدمت قبلاً یک رکورد نصب ثبت شده است.")

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            today = timezone.now().strftime("%y%m%d")
            prefix = "HRH"
            count = HolterHRInstallation.objects.filter(
                install_datetime__date=timezone.now().date()
            ).count() + 1
            self.tracking_code = f"{prefix}-{today}-{count:04d}"

        if self.reception_service and not self.patient_id:
            self.patient = self.reception_service.reception.patient

        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('holter_hr:holter_hr_detail', kwargs={'pk': self.pk})


class HolterHRReception(models.Model):
    installation = models.OneToOneField(
        HolterHRInstallation,
        on_delete=models.CASCADE,
        related_name="reception_record",
        verbose_name="رکورد نصب"
    )
    receive_datetime = models.DateTimeField(verbose_name="زمان و تاریخ دریافت")
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="کاربر دریافت‌کننده"
    )
    device_condition_on_return = models.TextField(blank=True, null=True, verbose_name="وضعیت دستگاه در بازگشت")
    patient_feedback = models.TextField(blank=True, null=True, verbose_name="بازخورد بیمار")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌های دریافت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "دریافت هلتر ضربان"
        verbose_name_plural = "دریافت‌های هلتر ضربان"
        ordering = ['-receive_datetime']
        indexes = [
            models.Index(fields=["receive_datetime"]),
            models.Index(fields=["installation"]),
        ]

    def __str__(self):
        patient_name = getattr(getattr(self.installation, 'patient', None), 'full_name', lambda: '---')()
        return f"دریافت هلتر از {patient_name} در تاریخ {self.receive_datetime.strftime('%Y-%m-%d')}"

    def clean(self):
        if self.receive_datetime < self.installation.install_datetime:
            raise ValidationError("زمان دریافت نمی‌تواند قبل از زمان نصب باشد.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return self.installation.get_absolute_url()


class HolterHRReading(models.Model):
    installation = models.OneToOneField(
        HolterHRInstallation,
        on_delete=models.CASCADE,
        related_name="reading",
        verbose_name="رکورد نصب"
    )
    read_datetime = models.DateTimeField(verbose_name="زمان و تاریخ خواندن")
    interpreted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="تحلیل‌گر"
    )

    # فیلدهای کلیدی تحلیل ضربان
    avg_heart_rate = models.PositiveIntegerField("میانگین ضربان قلب", null=True, blank=True)
    min_heart_rate = models.PositiveIntegerField("کمترین ضربان قلب", null=True, blank=True)
    min_hr_time = models.TimeField("زمان کمترین ضربان", null=True, blank=True)
    max_heart_rate = models.PositiveIntegerField("بیشترین ضربان قلب", null=True, blank=True)
    max_hr_time = models.TimeField("زمان بیشترین ضربان", null=True, blank=True)

    # HRV metrics
    sdnn = models.FloatField("SDNN", null=True, blank=True)
    rmssd = models.FloatField("RMSSD", null=True, blank=True)
    pnn50 = models.FloatField("pNN50", null=True, blank=True)

    summary = models.TextField(blank=True, null=True, verbose_name="خلاصه خوانش")
    report_file = models.FileField(upload_to="holter_reports/hr/", blank=True, null=True,
                                   verbose_name="فایل گزارش نهایی")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت خوانش")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "خواندن هلتر ضربان"
        verbose_name_plural = "خوانش‌های هلتر ضربان"
        ordering = ['-read_datetime']
        indexes = [
            models.Index(fields=["read_datetime"]),
            models.Index(fields=["installation"]),
        ]

    def __str__(self):
        patient_name = getattr(getattr(self.installation, 'patient', None), 'full_name', lambda: '---')()
        return f"خوانش برای {patient_name} - {self.read_datetime.strftime('%Y/%m/%d')}"

    def clean(self):
        if self.read_datetime and self.installation and self.read_datetime < self.installation.install_datetime:
            raise ValidationError("زمان خواندن نمی‌تواند قبل از نصب باشد.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return self.installation.get_absolute_url()
