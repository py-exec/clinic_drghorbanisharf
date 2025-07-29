from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


# ----------------------------
# عنوان شغلی
# ----------------------------
class StaffPosition(models.Model):
    title = models.CharField("عنوان شغلی", max_length=100, unique=True)
    description = models.TextField("توضیحات", blank=True)
    created_at = models.DateTimeField("ایجاد شده در", auto_now_add=True)

    class Meta:
        verbose_name = "عنوان شغلی"
        verbose_name_plural = "عناوین شغلی"
        ordering = ["title"]

    def __str__(self):
        return self.title


# ----------------------------
# اطلاعات کارمندان
# ----------------------------
class Staff(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        verbose_name="کاربر مرتبط"
    )
    position = models.ForeignKey(
        StaffPosition,
        on_delete=models.PROTECT,
        related_name="staffs",
        verbose_name="عنوان شغلی"
    )
    contract_number = models.CharField("شماره قرارداد", max_length=50, unique=True)
    contract_start = models.DateField("تاریخ شروع همکاری")
    contract_end = models.DateField("تاریخ پایان همکاری", null=True, blank=True)
    contract_file = models.FileField("فایل قرارداد", upload_to="staffs/contracts/", null=True, blank=True)

    base_salary = models.DecimalField("حقوق پایه ماهانه", max_digits=10, decimal_places=0, default=0)
    is_active = models.BooleanField("فعال", default=True)
    notes = models.TextField("یادداشت منابع انسانی", blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_staffs",
        verbose_name="ایجاد شده توسط"
    )
    created_at = models.DateTimeField("ایجاد شده در", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "کارمند"
        verbose_name_plural = "کارمندان"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name()} / {self.position.title}"


# ----------------------------
# حضور فیزیکی / اثر انگشت / کارت‌خوان
# ----------------------------
class AttendanceRecord(models.Model):
    METHOD_CHOICES = (
        ("manual", "ثبت دستی"),
        ("finger", "اثر انگشت"),
        ("card", "کارت‌خوان"),
        ("device", "دستگاه حضور و غیاب"),
    )

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="attendances", verbose_name="کارمند")
    date = models.DateField("تاریخ")
    clock_in = models.TimeField("ساعت ورود", null=True, blank=True)
    clock_out = models.TimeField("ساعت خروج", null=True, blank=True)
    method = models.CharField("روش ثبت", choices=METHOD_CHOICES, max_length=20, default="manual")
    note = models.TextField("توضیحات", blank=True)

    created_at = models.DateTimeField("ثبت شده در", auto_now_add=True)

    class Meta:
        verbose_name = "حضور / غیاب"
        verbose_name_plural = "سوابق حضور / غیاب"
        unique_together = ("staff", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.staff} - {self.date}"


# ----------------------------
# درخواست مرخصی
# ----------------------------
class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = (
        ("daily", "مرخصی روزانه"),
        ("hourly", "مرخصی ساعتی"),
    )
    STATUS_CHOICES = (
        ("pending", "در انتظار تایید"),
        ("approved", "تایید شده"),
        ("rejected", "رد شده"),
    )

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="leaves", verbose_name="کارمند")
    leave_type = models.CharField("نوع مرخصی", max_length=10, choices=LEAVE_TYPE_CHOICES)
    reason = models.TextField("دلیل مرخصی")
    start_date = models.DateField("از تاریخ")
    end_date = models.DateField("تا تاریخ", null=True, blank=True)
    start_time = models.TimeField("از ساعت", null=True, blank=True)
    end_time = models.TimeField("تا ساعت", null=True, blank=True)

    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField("تاریخ درخواست", auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    verbose_name="تایید کننده")
    reviewed_at = models.DateTimeField("تاریخ بررسی", null=True, blank=True)

    class Meta:
        verbose_name = "درخواست مرخصی"
        verbose_name_plural = "درخواست‌های مرخصی"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.staff} / {self.leave_type} / {self.status}"


class Shift(models.Model):
    title = models.CharField("عنوان شیفت", max_length=100)
    start_time = models.TimeField("ساعت شروع")
    end_time = models.TimeField("ساعت پایان")

    def __str__(self):
        return self.title


# ----------------------------
# ارتباط با شیفت کاری
# ----------------------------
class ShiftAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="assigned_shifts", verbose_name="کارمند")
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, verbose_name="شیفت")
    assigned_at = models.DateTimeField("تاریخ تخصیص", auto_now_add=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                    verbose_name="تخصیص‌دهنده")

    class Meta:
        verbose_name = "تخصیص شیفت"
        verbose_name_plural = "شیفت‌های تخصیص یافته"
        unique_together = ("staff", "shift")


# ----------------------------
# ثبت گزارش اضافه‌کاری / تأخیر / خروج زود
# ----------------------------
class DailyWorkLog(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="work_logs", verbose_name="کارمند")
    date = models.DateField("تاریخ")
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, verbose_name="شیفت")
    is_late = models.BooleanField("تاخیر داشته؟", default=False)
    left_early = models.BooleanField("زودتر خارج شده؟", default=False)
    overtime_hours = models.DecimalField("ساعت اضافه کاری", max_digits=4, decimal_places=2, default=0)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                     verbose_name="تایید کننده")
    worked_hours = models.DecimalField("ساعات کارکرد", max_digits=4, decimal_places=2, default=0)
    notes = models.TextField("یادداشت", blank=True)

    class Meta:
        verbose_name = "لاگ کاری روزانه"
        verbose_name_plural = "لاگ‌های کاری روزانه"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.staff} - {self.date}"
