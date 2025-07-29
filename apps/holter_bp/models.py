# apps/holter_bp/models.py

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords

User = settings.AUTH_USER_MODEL


class HolterBPInstallation(models.Model):
    """
    مرحله اول: نصب دستگاه هلتر فشار. این مدل به عنوان رکورد اصلی عمل می‌کند.
    """
    # وابستگی اصلی به خدمت پذیرش شده
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reception_service = GenericForeignKey('content_type', 'object_id')

    # ✅ اتصال مستقیم به بیمار برای پایداری و کارایی بهتر
    patient = models.ForeignKey(
        "patient.Patient",
        on_delete=models.PROTECT,
        related_name="bp_holter_installations",
        verbose_name="بیمار"
    )

    # ✅ کد پیگیری برای مدیریت آسان‌تر
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
        related_name="bp_holter_installations_done",
        verbose_name="تکنسین نصب"
    )
    patient_education_given = models.BooleanField(default=False, verbose_name="آموزش به بیمار داده شده؟")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌های زمان نصب")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_bp_holter_installations",
        verbose_name="کاربر ثبت‌کننده"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "نصب هلتر فشار"
        verbose_name_plural = "نصب‌های هلتر فشار"
        ordering = ['-install_datetime']
        indexes = [
            models.Index(fields=["install_datetime"]),
            models.Index(fields=["tracking_code"]),
            models.Index(fields=["patient"]),
        ]

    def __str__(self):
        patient_name = getattr(self.patient, 'full_name', lambda: '---')()
        return f"نصب هلتر فشار برای {patient_name} در تاریخ {self.install_datetime.strftime('%Y-%m-%d')}"

    def clean(self):
        super().clean()
        if self.install_datetime > timezone.now():
            raise ValidationError("تاریخ نصب نمی‌تواند در آینده باشد.")

        # ✅ اعتبارسنجی تداخلی بیمار
        if self.reception_service and self.reception_service.reception.patient != self.patient:
            raise ValidationError("بیمار انتخاب‌شده با بیمار ثبت‌شده در پذیرش مطابقت ندارد.")

        # ✅ جلوگیری از ثبت چند نصب برای یک خدمت
        if self.pk is None and self.__class__.objects.filter(content_type=self.content_type,
                                                             object_id=self.object_id).exists():
            raise ValidationError("برای این خدمت قبلاً یک رکورد نصب ثبت شده است.")

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            today = timezone.now().strftime("%y%m%d")
            prefix = "BPH"
            count = HolterBPInstallation.objects.filter(
                install_datetime__date=timezone.now().date()
            ).count() + 1
            self.tracking_code = f"{prefix}-{today}-{count:04d}"

        # اطمینان از اینکه بیمار از روی سرویس پذیرش ست شده
        if self.reception_service and not self.patient_id:
            self.patient = self.reception_service.reception.patient

        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('holter_bp:holter_bp_detail', kwargs={'pk': self.pk})


class HolterBPReception(models.Model):
    installation = models.OneToOneField(
        HolterBPInstallation,
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
        verbose_name = "دریافت هلتر فشار"
        verbose_name_plural = "دریافت‌های هلتر فشار"
        ordering = ['-receive_datetime']
        indexes = [
            models.Index(fields=["receive_datetime"]),
            models.Index(fields=["installation"]),
        ]

    def __str__(self):
        # ✅ پایدارسازی متد
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


# در فایل apps/holter_bp/models.py

class HolterBPReading(models.Model):
    """
    مرحله سوم: خوانش و تحلیل داده‌های دستگاه هلتر و ثبت گزارش نهایی.
    """
    installation = models.OneToOneField(
        HolterBPInstallation,
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

    #  فیلدهای جدید برای مقادیر کلیدی فشار خون
    # --- فشار سیستولیک (Systolic) ---
    avg_systolic_bp = models.PositiveIntegerField("میانگین فشار سیستولیک", null=True, blank=True)
    min_systolic_bp = models.PositiveIntegerField("کمترین فشار سیستولیک", null=True, blank=True)
    min_systolic_time = models.TimeField("زمان کمترین فشار سیستولیک", null=True, blank=True)
    max_systolic_bp = models.PositiveIntegerField("بیشترین فشار سیستولیک", null=True, blank=True)
    max_systolic_time = models.TimeField("زمان بیشترین فشار سیستولیک", null=True, blank=True)

    # --- فشار دیاستولیک (Diastolic) ---
    avg_diastolic_bp = models.PositiveIntegerField("میانگین فشار دیاستولیک", null=True, blank=True)
    min_diastolic_bp = models.PositiveIntegerField("کمترین فشار دیاستولیک", null=True, blank=True)
    min_diastolic_time = models.TimeField("زمان کمترین فشار دیاستولیک", null=True, blank=True)
    max_diastolic_bp = models.PositiveIntegerField("بیشترین فشار دیاستولیک", null=True, blank=True)
    max_diastolic_time = models.TimeField("زمان بیشترین فشار دیاستولیک", null=True, blank=True)

    summary = models.TextField(blank=True, null=True, verbose_name="خلاصه خوانش")
    report_file = models.FileField(upload_to="holter_reports/bp/", blank=True, null=True,
                                   verbose_name="فایل گزارش نهایی")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت خوانش")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "خواندن هلتر فشار"
        verbose_name_plural = "خوانش‌های هلتر فشار"
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
