from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.patient.models import Patient
from apps.doctors.models import Doctor

User = get_user_model()

# ====== BaseModel ======
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ===== وضعیت تست‌های پاراکلینیک =====
class TestStatus(models.TextChoices):
    NEEDED = "needed", "نیاز هست"
    DONE = "done", "انجام شده"
    UNKNOWN = "unknown", "نامشخص"


# ===== نسخه =====
class Prescription(TimeStampedModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_prescriptions")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="prescriptions", verbose_name="پزشک معالج")
    created_at = models.DateTimeField(default=timezone.now)

    # خلاصه تشخیصی
    symptom_onset = models.DateField("تاریخ شروع علائم", null=True, blank=True)
    angiography_result = models.TextField("نتیجه آنژیوگرافی", null=True, blank=True)

    # پیگیری نهایی
    followup_plan = models.TextField("توصیه به پیگیری", null=True, blank=True)

    REFERRAL_CHOICES = [
        ("none", "ندارد"),
        ("neurology", "نورولوژی"),
        ("electrophysiology", "ریتمولوژی"),
        ("general_surgery", "جراحی عمومی"),
    ]
    referral_specialist = models.CharField(
        "ارجاع به تخصص دیگر", max_length=50,
        choices=REFERRAL_CHOICES, null=True, blank=True
    )

    final_doctor_note = models.TextField("نظر نهایی پزشک", null=True, blank=True)
    review_date = models.DateField("تاریخ بررسی", null=True, blank=True)
    doctor_name = models.CharField("نام پزشک", max_length=100, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "نسخه پزشک"
        verbose_name_plural = "نسخه‌ها"

    def __str__(self):
        return f"نسخه {self.patient.full_name} - {self.created_at.strftime('%Y-%m-%d')}"


# ===== داروهای نسخه =====
class PrescriptionMedication(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField("نام دارو", max_length=100)
    dose = models.CharField("دوز", max_length=50)
    total = models.PositiveIntegerField("تعداد کل")
    per_day = models.PositiveIntegerField("مصرف روزانه")
    med_type = models.CharField("نوع مصرف", max_length=30, choices=[
        ("oral", "خوراکی"),
        ("injectable", "تزریقی"),
        ("sublingual", "زیر زبانی")
    ])

    def __str__(self):
        return f"{self.name} ({self.dose})"

    class Meta:
        verbose_name = "داروی نسخه"
        verbose_name_plural = "داروهای نسخه"


# ===== درخواست تست‌ها =====
class TestRequest(models.Model):
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE, related_name="test_request")

    holter_ecg = models.CharField(max_length=20, choices=TestStatus.choices, default=TestStatus.UNKNOWN)
    holter_bp = models.CharField(max_length=20, choices=TestStatus.choices, default=TestStatus.UNKNOWN)
    tilt_test = models.CharField(max_length=20, choices=TestStatus.choices, default=TestStatus.UNKNOWN)
    stress_test = models.CharField(max_length=20, choices=TestStatus.choices, default=TestStatus.UNKNOWN)
    echo = models.CharField(max_length=20, choices=TestStatus.choices, default=TestStatus.UNKNOWN)
    tee = models.CharField("اکو مری", max_length=20, choices=TestStatus.choices, default=TestStatus.UNKNOWN)

    class Meta:
        verbose_name = "درخواست تست"
        verbose_name_plural = "درخواست‌های تست"


# ===== ارزیابی دستگاه =====
class DeviceAssessment(models.Model):
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE, related_name="device_assessment")
    device_type = models.CharField("نوع دستگاه", max_length=50, null=True, blank=True)
    battery_percent = models.PositiveSmallIntegerField("درصد باتری", null=True, blank=True)
    device_implant_date = models.DateField("تاریخ نصب", null=True, blank=True)
    shock_occurred = models.BooleanField("شوک ثبت شده؟", null=True, blank=True)
    lead_problem = models.BooleanField("لید دارای مشکل؟", null=True, blank=True)
    notes = models.TextField("یادداشت پزشک درباره دستگاه", null=True, blank=True)

    class Meta:
        verbose_name = "ارزیابی دستگاه قلبی"
        verbose_name_plural = "ارزیابی‌های دستگاه قلبی"


# ===== برنامه جراحی =====
class SurgeryPlan(TimeStampedModel):
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE, related_name="surgery_plan")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ثبت‌کننده")

    # نیازهای جراحی
    need_battery_replacement = models.BooleanField("نیاز به تعویض باتری؟", null=True, blank=True)
    need_lead_revision = models.BooleanField("نیاز به اصلاح یا تعویض لید؟", null=True, blank=True)
    need_device_extraction = models.BooleanField("نیاز به استخراج دستگاه؟", null=True, blank=True)
    general_surgery_needed = models.BooleanField("نیاز به جراحی عمومی دیگر؟", null=True, blank=True)
    general_surgery_reason = models.TextField("توضیح درباره جراحی عمومی", null=True, blank=True)

    # نوع جراحی پیشنهادی
    suggested_surgery_type = models.CharField(
        "نوع جراحی پیشنهادی", max_length=100, null=True, blank=True,
        choices=[
            ("battery_change", "تعویض باتری"),
            ("lead_revision", "تعویض لید"),
            ("extraction", "خارج‌سازی"),
            ("reimplant", "کاشت مجدد"),
            ("exploration", "بررسی تخصصی بیشتر"),
            ("general", "جراحی عمومی")
        ]
    )
    suggested_surgery_note = models.TextField("توضیحات جراحی", null=True, blank=True)

    # محل پیشنهادی نصب
    implant_location = models.CharField(
        "محل پیشنهادی نصب", max_length=100, null=True, blank=True,
        choices=[
            ("left_submuscular", "زیر عضله چپ"),
            ("right_subcutaneous", "زیر جلد راست"),
            ("previous_site", "محل قبلی"),
            ("other", "سایر")
        ]
    )
    implant_location_note = models.TextField("توضیحات محل نصب", null=True, blank=True)

    # ارجاع و زمان
    preferred_surgery_date = models.DateField("تاریخ پیشنهادی", null=True, blank=True)
    surgery_center = models.CharField("مرکز جراحی ارجاعی", max_length=150, null=True, blank=True)
    surgeon_name = models.CharField("نام جراح", max_length=150, null=True, blank=True)

    # یادداشت نهایی
    doctor_notes = models.TextField("یادداشت نهایی پزشک", null=True, blank=True)

    class Meta:
        verbose_name = "برنامه جراحی"
        verbose_name_plural = "برنامه‌های جراحی"
        ordering = ["-created_at"]

    def __str__(self):
        return f"برنامه جراحی نسخه #{self.prescription.id} - {self.prescription.patient.full_name}"