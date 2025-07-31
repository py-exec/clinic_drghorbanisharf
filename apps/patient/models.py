# apps/patient/models.py
import re
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords # Uncomment if you use django-simple-history

User = settings.AUTH_USER_MODEL # It's better to use get_user_model() in apps, but for settings.AUTH_USER_MODEL it's fine.
                                # Or define: from django.contrib.auth import get_user_model; User = get_user_model()


# CHOICES for Patient model
BLOOD_GROUP_CHOICES = [
    ("", "انتخاب کنید..."),
    ("A+", "A+"), ("A-", "A-"),
    ("B+", "B+"), ("B-", "B-"),
    ("AB+", "AB+"), ("AB-", "AB-"),
    ("O+", "O+"), ("O-", "O-"),
]

MOBILITY_STATUS_CHOICES = [
    ("", "انتخاب کنید..."),
    ("independent", "مستقل"),
    ("wheelchair", "نیازمند ویلچر"),
    ("bedridden", "زمین‌گیر"),
]

HEALTH_LITERACY_CHOICES = [
    ("", "انتخاب کنید..."),
    ("low", "پایین"),
    ("medium", "متوسط"),
    ("high", "بالا"),
]

INSURANCE_CATEGORY_CHOICES = [
    ("", "انتخاب کنید..."),
    ("basic", "بیمه پایه"),
    ("supplementary", "بیمه تکمیلی"),
    ("other", "سایر"),
]

INSURANCE_COMPANY_CHOICES = [
    ("", "انتخاب کنید..."),
    ("tamin", "تأمین اجتماعی"),
    ("salamat", "سلامت"),
    ("iran", "بیمه ایران"),
    ("asia", "بیمه آسیا"),
    ("dana", "بیمه دانا"),
    ("alborz", "بیمه البرز"),
    ("kosar", "بیمه کوثر"),
    ("mellat", "بیمه ملت"),
    ("sina", "بیمه سینا"),
    ("moalem", "بیمه معلم"),
    ("novin", "بیمه نوین"),
    ("pasargad", "بیمه پاسارگاد"),
    ("other", "سایر"),
]


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        verbose_name="کاربر مرتبط",
    )

    # اطلاعات پایه بیمار
    record_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="شماره پرونده",
        blank=True,
        db_index=True,
    )
    total_receptions = models.PositiveIntegerField(default=0, verbose_name="تعداد کل پذیرش‌ها")

    # اطلاعات پزشکی ثابت یا عمومی بیمار
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, verbose_name="گروه خونی")
    has_allergy = models.BooleanField(default=False, verbose_name="آیا آلرژی دارید؟")
    allergy_info = models.TextField(blank=True, verbose_name="توضیحات آلرژی")
    mobility_status = models.CharField(
        max_length=50, choices=MOBILITY_STATUS_CHOICES, blank=True, verbose_name="وضعیت توان حرکتی"
    )
    special_needs = models.CharField(max_length=100, blank=True, verbose_name="نیاز به خدمات ویژه")
    health_literacy = models.CharField(
        max_length=20, choices=HEALTH_LITERACY_CHOICES, blank=True, verbose_name="سواد سلامت"
    )

    # بیمه و ارجاع
    basic_insurance_company = models.CharField(
        max_length=50,
        choices=INSURANCE_COMPANY_CHOICES,
        blank=True,
        verbose_name="شرکت بیمه پایه"
    )
    basic_insurance_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره بیمه پایه"
    )
    basic_insurance_file = models.FileField(
        upload_to='insurance/basic/',
        blank=True,
        null=True,
        verbose_name="کارت بیمه پایه"
    )
    supplementary_insurance_company = models.CharField(
        max_length=50,
        choices=INSURANCE_COMPANY_CHOICES,
        blank=True,
        verbose_name="شرکت بیمه تکمیلی"
    )
    supplementary_insurance_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره بیمه تکمیلی"
    )
    supplementary_insurance_file = models.FileField(
        upload_to='insurance/supplementary/',
        blank=True,
        null=True,
        verbose_name="کارت بیمه تکمیلی"
    )

    is_referred = models.BooleanField(default=False, verbose_name="بیمه ارجاعی است؟")
    referring_doctor = models.CharField(max_length=100, blank=True, verbose_name="پزشک ارجاع دهنده")
    referring_center = models.CharField(max_length=100, blank=True, verbose_name="مرکز ارجاع")
    referral_file = models.FileField(upload_to='referrals/', blank=True, null=True, verbose_name="فایل ارجاع")

    # همراه
    companion_name = models.CharField(max_length=100, blank=True, verbose_name="نام همراه")
    companion_relation = models.CharField(max_length=50, blank=True, verbose_name="نسبت همراه")
    companion_phone = models.CharField(max_length=11, blank=True, verbose_name="شماره تماس همراه")
    companion_decision = models.BooleanField(default=False, verbose_name="اجازه تصمیم گیری دارد؟")

    # تاریخچه - اگر از django-simple-history استفاده می‌کنید، خط زیر را از کامنت خارج کنید.
    # history = HistoricalRecords()

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="تاریخ بروزرسانی")

    def __str__(self):
        if self.user:
            # مطمئن شوید که User مدل دارای فیلد national_code است
            return f"{self.user.get_full_name()} ({self.user.national_code if hasattr(self.user, 'national_code') else 'N/A'})"
        return f"بیمار بدون کاربر ({self.record_number})"

    class Meta:
        verbose_name = "بیمار"
        verbose_name_plural = "بیماران"

    def save(self, *args, **kwargs):
        if not self.record_number:
            try:
                self.record_number = self.generate_record_number()
            except Exception as e:
                import logging
                logging.error(f"⚠️ خطا در تولید شماره پرونده: {e}")
                raise ValueError("❌ تولید شماره پرونده با شکست مواجه شد.")
        super().save(*args, **kwargs)

    def generate_record_number(self):
        prefix = "PY"
        pattern = re.compile(rf"^{prefix}-(\d+)$")
        last_numbers = (
            Patient.objects
            .filter(record_number__startswith=prefix)
            .values_list('record_number', flat=True)
        )
        valid_numbers = []
        for rn in last_numbers:
            match = pattern.match(rn)
            if match:
                try:
                    valid_numbers.append(int(match.group(1)))
                except ValueError:
                    continue # Skip invalid numbers
        next_number = max(valid_numbers or [0]) + 1
        if next_number > 999999:
            raise ValueError("حداکثر ظرفیت شماره پرونده‌ها پر شده است.")
        return f"{prefix}-{next_number:05d}"

    # فایل‌های پزشکی
    def get_files_by_category(self, category):
        return self.files.filter(category=category)

    def ecg_files(self):
        return self.get_files_by_category("ecg")

    def holter_files(self):
        return self.get_files_by_category("holter")

    def lab_files(self):
        return self.get_files_by_category("lab")

    def imaging_files(self):
        return self.get_files_by_category("imaging")

    def other_files(self):
        return self.get_files_by_category("other")

    def full_name(self):
        # Ensure User model has first_name and last_name
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def national_id(self):
        # Assuming User model has a 'national_code' field.
        return self.user.national_code if hasattr(self.user, 'national_code') else None

    @property
    def date_of_birth(self):
        # Assuming User model has a 'date_of_birth' field.
        return self.user.date_of_birth if hasattr(self.user, 'date_of_birth') else None

    @property
    def latest_service_level(self):
        # اگر Patient به Reception وصل هست (فرض می‌کنیم related_name="receptions")
        # نیاز به اطمینان از وجود مدل Reception و فیلد admission_date و service_level در آن
        if hasattr(self, 'receptions'):
            latest = self.receptions.order_by('-admission_date').first()
            return latest.service_level if latest else "—"
        return "—" # Return default if no receptions or attribute doesn't exist

    def get_absolute_url(self):
        return reverse('patient:patient_detail', kwargs={'pk': self.pk})


class PatientFile(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="files", verbose_name="بیمار")
    title = models.CharField(max_length=255, verbose_name="عنوان فایل")
    file = models.FileField(upload_to="patient_files/", verbose_name="فایل پزشکی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    category = models.CharField(
        max_length=50,
        choices=[
            ("ecg", "نوار قلب"),
            ("holter", "هولتر"),
            ("lab", "آزمایش"),
            ("imaging", "تصویربرداری"),
            ("other", "سایر"),
        ],
        verbose_name="نوع فایل"
    )

    related_ecg = models.ForeignKey(
        "ecg.ECGRecord", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="patient_files", verbose_name="مرتبط با نوار قلب"
    )

    related_holter = models.ForeignKey(
        "holter.HolterDevice", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="patient_files", verbose_name="مرتبط با هولتر"
    )

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="آپلودکننده")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان آپلود")

    class Meta:
        verbose_name = "فایل پزشکی"
        verbose_name_plural = "فایل‌های پزشکی بیمار"
        ordering = ["-uploaded_at"]

    def __str__(self):
        patient_name = self.patient.full_name()
        return f"{patient_name} | {self.title or self.category} | {self.uploaded_at.date()}"

    def get_absolute_url(self):
        """
        آدرس کانونیکال این فایل را برمی‌گرداند (که همان صفحه جزئیات بیمار است).
        """
        return self.patient.get_absolute_url()