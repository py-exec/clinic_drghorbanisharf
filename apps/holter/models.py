from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.prescriptions.models import Prescription


User = get_user_model()


### وضعیت دستگاه
class HolterStatus(models.TextChoices):
    IN_CLINIC = "in_clinic", "در کلینیک"
    ASSIGNED_TO_PATIENT = "assigned", "امانت بیمار"
    READY = "ready", "آماده استفاده"
    WAITING_FOR_REPAIR = "waiting_repair", "در انتظار تعمیر"
    UNDER_REPAIR = "repairing", "در حال تعمیر"
    BROKEN = "broken", "غیر قابل استفاده"

### دستگاه هولتر
class HolterDevice(models.Model):
    inventory_item = models.ForeignKey(
        "inventory.Item", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="holter_devices", verbose_name="کالای انبار"
    )

    serial_number = models.CharField("شماره سریال", max_length=100, unique=True)
    asset_code = models.CharField("شماره اموال", max_length=100, unique=True, null=True, blank=True)
    internal_code = models.CharField("کد داخلی / QR", max_length=50, unique=True, null=True, blank=True)
    model_name = models.CharField("مدل دستگاه", max_length=100)

    device_type = models.CharField(
        "نوع دستگاه", max_length=20,
        choices=[('bp', 'فشار خون'), ('hr', 'ضربان قلب'), ('combo', 'فشار + ضربان')]
    )

    status = models.CharField("وضعیت", max_length=30, choices=HolterStatus.choices, default=HolterStatus.IN_CLINIC)
    patient = models.ForeignKey("patient.Patient", on_delete=models.SET_NULL, null=True, blank=True, related_name="current_holters")
    last_used_by = models.ForeignKey("patient.Patient", on_delete=models.SET_NULL, null=True, blank=True, related_name="used_holters")
    assigned_until = models.DateTimeField("تا تاریخ", null=True, blank=True)

    battery_status = models.CharField("وضعیت باتری", max_length=100, null=True, blank=True)
    firmware_version = models.CharField("نسخه نرم‌افزار", max_length=50, null=True, blank=True)
    is_calibrated = models.BooleanField("کالیبره شده؟", default=True)
    last_maintenance = models.DateField("آخرین سرویس", null=True, blank=True)
    warranty_expiry = models.DateField("پایان گارانتی", null=True, blank=True)
    health_note = models.TextField("یادداشت فنی", null=True, blank=True)

    is_active = models.BooleanField("فعال است؟", default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "دستگاه هولتر"
        verbose_name_plural = "دستگاه‌های هولتر"

    def __str__(self):
        return f"{self.model_name} | {self.serial_number}"

    def is_usable(self):
        return self.status in [HolterStatus.READY, HolterStatus.IN_CLINIC] and self.is_active

class HolterStatusLog(models.Model):
    device = models.ForeignKey(HolterDevice, on_delete=models.CASCADE, related_name="status_logs")
    old_status = models.CharField(max_length=30, choices=HolterStatus.choices)
    new_status = models.CharField(max_length=30, choices=HolterStatus.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تاریخچه وضعیت دستگاه"
        verbose_name_plural = "تاریخچه‌های وضعیت دستگاه"

class HolterAssignment(models.Model):
    device = models.ForeignKey(HolterDevice, on_delete=models.CASCADE, related_name="assignments")
    patient = models.ForeignKey("patient.Patient", on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "سابقه امانت دستگاه"
        verbose_name_plural = "سوابق امانت"

class HolterInstallation(models.Model):
    device = models.ForeignKey(HolterDevice, on_delete=models.CASCADE, related_name="installations")
    patient = models.ForeignKey("patient.Patient", on_delete=models.CASCADE)
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="holter_installations",
        verbose_name="نسخه مرتبط"
    )

    install_datetime = models.DateTimeField("تاریخ و ساعت نصب", null=True, blank=True)
    technician_name = models.CharField("تکنسین", max_length=100)
    location = models.CharField("محل نصب", max_length=255, null=True, blank=True)

    notes = models.TextField("یادداشت", null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نصب دستگاه"
        verbose_name_plural = "نصب‌ها"


class HolterRepairLog(models.Model):
    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("in_progress", "در حال تعمیر"),
        ("done", "تعمیر شده"),
        ("discarded", "غیرفعال/اسقاط شده"),
    ]

    device = models.ForeignKey(
        HolterDevice,
        on_delete=models.CASCADE,
        related_name="repairs",
        verbose_name="دستگاه"
    )

    issue_description = models.TextField("شرح مشکل")
    status = models.CharField("وضعیت تعمیر", max_length=20, choices=STATUS_CHOICES, default="pending")

    repair_start = models.DateField("تاریخ شروع")
    repair_end = models.DateField("تاریخ پایان", null=True, blank=True)

    cost = models.DecimalField("هزینه تعمیر (تومان)", max_digits=12, decimal_places=0, null=True, blank=True)
    repaired_by = models.CharField("نام تعمیرکار", max_length=100)
    resolution_notes = models.TextField("یادداشت تکمیلی", null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ثبت توسط"
    )
    created_at = models.DateTimeField("تاریخ ثبت", default=timezone.now)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        verbose_name = "گزارش تعمیر دستگاه هولتر"
        verbose_name_plural = "تعمیرات دستگاه‌های هولتر"
        ordering = ["-repair_start"]

    def __str__(self):
        return f"{self.device} | {self.repair_start} - {self.status}"

    def duration(self):
        """مدت زمان تعمیر (روز)"""
        if self.repair_start and self.repair_end:
            return (self.repair_end - self.repair_start).days
        return None

    def is_completed(self):
        return self.status == "done"