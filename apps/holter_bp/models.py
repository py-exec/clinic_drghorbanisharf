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
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reception_service = GenericForeignKey('content_type', 'object_id')

    patient = models.ForeignKey(
        "patient.Patient",
        on_delete=models.PROTECT,
        related_name="bp_holter_installations",
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

    # NEW: Latest status for this specific installation stage
    latest_installation_status = models.CharField(
        max_length=20,
        choices=[
            ('installed', 'نصب شده'),
            ('reinstalled', 'نصب مجدد'),
            ('cancelled', 'لغو نصب'),
            ('failed', 'ناموفق'),
            ('on_hold', 'در انتظار'),  # مثلا منتظر قطعه خاصی
        ],
        default='installed',  # وضعیت پیش‌فرض پس از ثبت موفق نصب
        verbose_name="آخرین وضعیت نصب"
    )

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
        if self.reception_service and self.reception_service.reception.patient != self.patient:
            raise ValidationError("بیمار انتخاب‌شده با بیمار ثبت‌شده در پذیرش مطابقت ندارد.")
        if self.pk is None and self.__class__.objects.filter(content_type=self.content_type,
                                                             object_id=self.object_id).exists():
            raise ValidationError("برای این خدمت قبلاً یک رکورد نصب ثبت شده است.")

        # Add validation for device (similar to what was discussed for Holter HR)
        # Assuming Item model has 'category' and 'name' that can identify Holter BP devices
        # Example:
        # if self.device:
        #     if self.device.category != 'equipment' or 'هولتر' not in self.device.name or 'فشار' not in self.device.name:
        #         raise ValidationError(
        #             {'device': "دستگاه انتخاب شده یک دستگاه هلتر فشار معتبر نیست. لطفاً یک 'تجهیزات پزشکی' با نام 'هولتر فشار' انتخاب کنید."}
        #         )

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Check if this is a new instance

        if not self.tracking_code:
            today = timezone.now().strftime("%y%m%d")
            prefix = "BPH"  # Changed prefix for Holter BP
            count = HolterBPInstallation.objects.filter(
                install_datetime__date=timezone.now().date()
            ).count() + 1
            self.tracking_code = f"{prefix}-{today}-{count:04d}"

        if self.reception_service and not self.patient_id:
            self.patient = self.reception_service.reception.patient

        self.full_clean()
        super().save(*args, **kwargs)

        # NEW: Create an initial status record if this is a new installation
        if is_new:
            HolterBPInstallationStatus.objects.create(
                installation=self,
                status=self.latest_installation_status,  # Use the default or set it
                changed_by=self.created_by,  # Assuming created_by is the user who made the record
                note="رکورد نصب جدید هلتر فشار ثبت شد."
            )

    def get_absolute_url(self):
        return reverse('holter_bp:holter_bp_detail', kwargs={'pk': self.pk})


class HolterBPInstallationStatus(models.Model):
    """
    تاریخچه وضعیت‌های مرحله نصب دستگاه هلتر فشار.
    """
    STATUS_CHOICES = [
        ('installed', 'نصب شده'),
        ('reinstalled', 'نصب مجدد'),
        ('cancelled', 'لغو نصب'),
        ('failed', 'ناموفق'),
        ('on_hold', 'در انتظار'),
        # ... سایر وضعیت‌های داخلی مرحله نصب ...
    ]
    installation = models.ForeignKey(
        HolterBPInstallation,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="نصب مربوطه"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="وضعیت نصب"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت وضعیت")
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="تغییر دهنده وضعیت"
    )
    note = models.TextField(blank=True, null=True, verbose_name="یادداشت وضعیت")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="مدت این وضعیت (ثانیه)")

    class Meta:
        ordering = ['timestamp']
        verbose_name = "وضعیت نصب هلتر فشار"
        verbose_name_plural = "وضعیت‌های نصب هلتر فشار"

    def __str__(self):
        return f"نصب BP #{self.installation.pk} - وضعیت: {self.get_status_display()} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update previous status duration
        previous = (
            HolterBPInstallationStatus.objects
            .filter(installation=self.installation)
            .exclude(pk=self.pk)
            .order_by("-timestamp")
            .first()
        )
        if previous and previous.duration_seconds == 0:
            delta = (self.timestamp - previous.timestamp).total_seconds()
            previous.duration_seconds = max(1, int(delta))
            previous.save(update_fields=["duration_seconds"])

        # Update latest_installation_status on HolterBPInstallation
        if self.installation.latest_installation_status != self.status:
            self.installation.latest_installation_status = self.status
            self.installation.save(update_fields=["latest_installation_status"])


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

    # NEW: Latest status for this specific reception stage
    latest_reception_status = models.CharField(
        max_length=25,
        choices=[
            ('received', 'دریافت شده'),
            ('damaged_on_return', 'آسیب دیده در بازگشت'),
            ('missing_accessories', 'کسر قطعات'),
            ('on_hold_for_inspection', 'در انتظار بازرسی'),
        ],
        default='received',
        verbose_name="آخرین وضعیت دریافت"
    )

    class Meta:
        verbose_name = "دریافت هلتر فشار"
        verbose_name_plural = "دریافت‌های هلتر فشار"
        ordering = ['-receive_datetime']
        indexes = [
            models.Index(fields=["receive_datetime"]),
            models.Index(fields=["installation"]),
        ]

    def __str__(self):
        patient_name = getattr(getattr(self.installation, 'patient', None), 'full_name', lambda: '---')()
        return f"دریافت هلتر فشار از {patient_name} در تاریخ {self.receive_datetime.strftime('%Y-%m-%d')}"

    def clean(self):
        if self.receive_datetime < self.installation.install_datetime:
            raise ValidationError("زمان دریافت نمی‌تواند قبل از زمان نصب باشد.")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.full_clean()
        super().save(*args, **kwargs)

        # NEW: Create an initial status record if this is a new reception
        if is_new:
            HolterBPReceptionStatus.objects.create(
                reception=self,
                status=self.latest_reception_status,
                changed_by=self.received_by,  # Assuming received_by is the appropriate user
                note="رکورد دریافت جدید هلتر فشار ثبت شد."
            )

    def get_absolute_url(self):
        return self.installation.get_absolute_url()


class HolterBPReceptionStatus(models.Model):
    """
    تاریخچه وضعیت‌های مرحله دریافت دستگاه هلتر فشار.
    """
    STATUS_CHOICES = [
        ('received', 'دریافت شده'),
        ('damaged_on_return', 'آسیب دیده در بازگشت'),
        ('missing_accessories', 'کسر قطعات'),
        ('on_hold_for_inspection', 'در انتظار بازرسی'),
        # ... سایر وضعیت‌های داخلی مرحله دریافت ...
    ]
    reception = models.ForeignKey(
        HolterBPReception,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="دریافت مربوطه"
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        verbose_name="وضعیت دریافت"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت وضعیت")
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="تغییر دهنده وضعیت"
    )
    note = models.TextField(blank=True, null=True, verbose_name="یادداشت وضعیت")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="مدت این وضعیت (ثانیه)")

    class Meta:
        ordering = ['timestamp']
        verbose_name = "وضعیت دریافت هلتر فشار"
        verbose_name_plural = "وضعیت‌های دریافت هلتر فشار"

    def __str__(self):
        return f"دریافت BP #{self.reception.pk} - وضعیت: {self.get_status_display()} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        previous = (
            HolterBPReceptionStatus.objects
            .filter(reception=self.reception)
            .exclude(pk=self.pk)
            .order_by("-timestamp")
            .first()
        )
        if previous and previous.duration_seconds == 0:
            delta = (self.timestamp - previous.timestamp).total_seconds()
            previous.duration_seconds = max(1, int(delta))
            previous.save(update_fields=["duration_seconds"])

        # Update latest_reception_status on HolterBPReception
        if self.reception.latest_reception_status != self.status:
            self.reception.latest_reception_status = self.status
            self.reception.save(update_fields=["latest_reception_status"])


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

    # NEW: Latest status for this specific reading stage
    latest_reading_status = models.CharField(
        max_length=20,
        choices=[
            ('in_analysis', 'در حال تحلیل'),
            ('analyzed', 'تحلیل شده'),
            ('reviewed', 'بازبینی شده'),
            ('finalized', 'نهایی شده'),
            ('rejected', 'رد شده'),  # مثلا به دلیل کیفیت پایین داده
            ('on_hold', 'در انتظار'),  # مثلا منتظر تایید پزشک
        ],
        default='in_analysis',
        verbose_name="آخرین وضعیت خوانش"
    )

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
        is_new = self._state.adding
        self.full_clean()
        super().save(*args, **kwargs)

        # NEW: Create an initial status record if this is a new reading
        if is_new:
            HolterBPReadingStatus.objects.create(
                reading=self,
                status=self.latest_reading_status,
                changed_by=self.interpreted_by,  # Assuming interpreted_by is the appropriate user
                note="رکورد خوانش جدید هلتر فشار ثبت شد."
            )

    def get_absolute_url(self):
        return self.installation.get_absolute_url()


class HolterBPReadingStatus(models.Model):
    """
    تاریخچه وضعیت‌های مرحله خوانش و تحلیل گزارش هلتر فشار.
    """
    STATUS_CHOICES = [
        ('in_analysis', 'در حال تحلیل'),
        ('analyzed', 'تحلیل شده'),
        ('reviewed', 'بازبینی شده'),
        ('finalized', 'نهایی شده'),
        ('rejected', 'رد شده'),  # مثلا به دلیل کیفیت پایین داده
        ('on_hold', 'در انتظار'),  # مثلا منتظر تایید پزشک
        # ... سایر وضعیت‌های داخلی مرحله خوانش ...
    ]
    reading = models.ForeignKey(
        HolterBPReading,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="خوانش مربوطه"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="وضعیت خوانش"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت وضعیت")
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="تغییر دهنده وضعیت"
    )
    note = models.TextField(blank=True, null=True, verbose_name="یادداشت وضعیت")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="مدت این وضعیت (ثانیه)")

    class Meta:
        ordering = ['timestamp']
        verbose_name = "وضعیت خوانش هلتر فشار"
        verbose_name_plural = "وضعیت‌های خوانش هلتر فشار"

    def __str__(self):
        return f"خوانش BP #{self.reading.pk} - وضعیت: {self.get_status_display()} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        previous = (
            HolterBPReadingStatus.objects
            .filter(reading=self.reading)
            .exclude(pk=self.pk)
            .order_by("-timestamp")
            .first()
        )
        if previous and previous.duration_seconds == 0:
            delta = (self.timestamp - previous.timestamp).total_seconds()
            previous.duration_seconds = max(1, int(delta))
            previous.save(update_fields=["duration_seconds"])

        # Update latest_reading_status on HolterBPReading
        if self.reading.latest_reading_status != self.status:
            self.reading.latest_reading_status = self.status
            self.reading.save(update_fields=["latest_reading_status"])