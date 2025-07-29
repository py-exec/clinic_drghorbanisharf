import re
from apps.reception.models import Location, Resource
from django.conf import settings
from django.core.exceptions import ValidationError  # برای استفاده در متد clean()
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


# ----------------------------
# دسته‌بندی تخصص‌ها (بدون تغییر)
# ----------------------------
class SpecialtyCategory(models.Model):
    title = models.CharField("عنوان دسته", max_length=100, unique=True)
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "دسته تخصص"
        verbose_name_plural = "دسته‌های تخصص"

    def __str__(self):
        return self.title


# ----------------------------
# تخصص‌ها (بدون تغییر)
# ----------------------------
class Specialty(models.Model):
    category = models.ForeignKey(SpecialtyCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="دسته‌بندی")
    title = models.CharField("عنوان تخصص", max_length=100, unique=True)
    description = models.TextField("توضیحات", blank=True)
    slug = models.SlugField("آدرس اینترنتی", max_length=150, unique=True, blank=True)

    class Meta:
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# ----------------------------
# اطلاعات پزشک (Doctor) - به‌روزرسانی نهایی
# ----------------------------
class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="کاربر")
    medical_code = models.CharField("شماره نظام پزشکی", max_length=20, unique=True)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, verbose_name="تخصص")
    slug = models.SlugField("آدرس اینترنتی", max_length=255, unique=True, blank=True)

    # فیلد جدید: ارتباط با شعبه/شعب
    locations = models.ManyToManyField(Location, blank=True, verbose_name="شعب فعالیت",
                                       help_text="شعبی که این پزشک در آن‌ها فعالیت می‌کند.")

    # اطلاعات حرفه‌ای (بدون تغییر)
    education = models.CharField("مدرک تحصیلی", max_length=200, blank=True)
    university = models.CharField("دانشگاه محل تحصیل", max_length=200, blank=True)
    work_experience = models.PositiveIntegerField("تجربه کاری (سال)", default=0)
    tags = models.CharField("برچسب‌ها (با ویرگول)", max_length=255, blank=True)
    bio = models.TextField("بیوگرافی", blank=True)

    # مطب (این فیلدها ممکن است با فیلد locations همپوشانی پیدا کنند و شاید نیاز به بازبینی داشته باشند)
    # در یک سیستم چند شعبه‌ای، آدرس مطب شاید بهتر باشد به Location یا DoctorSchedule مرتبط شود.
    # در حال حاضر آنها را نگه می‌داریم اما توجه داشته باشید که ممکن است در آینده به بازبینی نیاز داشته باشند.
    clinic_address = models.TextField("آدرس مطب", blank=True)
    clinic_phone = models.CharField("تلفن مطب", max_length=20, blank=True)
    clinic_location = models.CharField("موقعیت مکانی", max_length=255, blank=True)

    profile_image = models.ImageField("تصویر پروفایل", upload_to="doctors/profiles/", blank=True, null=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ثبت", default=timezone.now)

    class Meta:
        verbose_name = "پزشک"
        verbose_name_plural = "پزشکان"
        ordering = ["user__last_name"]
        indexes = [
            models.Index(fields=['medical_code']),
            models.Index(fields=['specialty']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        # 📌 اصلاح: بررسی وجود self.user قبل از فراخوانی get_full_name()
        if self.user:
            return self.user.get_full_name()
        return f"پزشک (کد نظام پزشکی: {self.medical_code})"

    def short_bio(self):
        return (self.bio[:75] + "...") if self.bio and len(self.bio) > 75 else self.bio

    def save(self, *args, **kwargs):
        # 📌 اصلاح: تولید slug فقط در صورت وجود user و عدم وجود slug
        if not self.slug and self.user and self.user.first_name and self.user.last_name:
            self.slug = slugify(self.user.get_full_name())
        elif not self.slug and self.medical_code:  # اگر user نبود، از medical_code استفاده کند
            self.slug = slugify(f"doctor-{self.medical_code}")
        super().save(*args, **kwargs)


# ----------------------------
# 🗓️ مدل برنامه کاری پزشک (DoctorSchedule) - نهایی
# ----------------------------
class DoctorSchedule(models.Model):
    """
    🗓️ DoctorSchedule

    این مدل برنامه کاری منظم (شیفت‌ها) هر پزشک را در یک شعبه خاص تعریف می‌کند.
    برای اعتبارسنجی نوبت‌دهی و اطمینان از اینکه نوبت‌ها فقط در زمان‌های کاری پزشک رزرو می‌شوند، استفاده می‌شود.
    """
    # 0=شنبه، 1=یکشنبه، ...، 6=جمعه (برای هماهنگی با تقویم شمسی/فارسی)
    DAY_OF_WEEK_CHOICES = [
        (0, 'شنبه'),
        (1, 'یکشنبه'),
        (2, 'دوشنبه'),
        (3, 'سه‌شنبه'),
        (4, 'چهارشنبه'),
        (5, 'پنج‌شنبه'),
        (6, 'جمعه'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="schedules", verbose_name="پزشک")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="شعبه فعالیت")
    day_of_week = models.IntegerField("روز هفته", choices=DAY_OF_WEEK_CHOICES,
                                      help_text="روزی از هفته که پزشک در آن فعال است (0=شنبه, 6=جمعه).")
    start_time = models.TimeField("ساعت شروع", help_text="ساعت شروع شیفت کاری.")
    end_time = models.TimeField("ساعت پایان", help_text="ساعت پایان شیفت کاری.")
    is_active = models.BooleanField("فعال", default=True,
                                    help_text="آیا این شیفت کاری در حال حاضر فعال است؟")

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "برنامه کاری پزشک"
        verbose_name_plural = "برنامه‌های کاری پزشکان"
        ordering = ["doctor", "day_of_week", "start_time"]
        indexes = [
            models.Index(fields=['doctor', 'location', 'day_of_week']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        # 📌 اصلاح: بررسی وجود self.doctor.user قبل از فراخوانی get_full_name()
        doctor_name = self.doctor.user.get_full_name() if self.doctor and self.doctor.user else "پزشک نامشخص"
        return f"شیفت {doctor_name} در {self.location.name} - {self.get_day_of_week_display()} از {self.start_time} تا {self.end_time}"

    def clean(self):
        super().clean()
        if self.start_time >= self.end_time:
            raise ValidationError("ساعت شروع شیفت نمی‌تواند بزرگتر یا مساوی ساعت پایان باشد.")

        # 📌 منطق دقیق‌تر برای بررسی تداخل با شیفت‌های دیگر
        # فقط شیفت‌های فعال را بررسی می‌کنیم
        conflicting_schedules = DoctorSchedule.objects.filter(
            doctor=self.doctor,
            location=self.location,
            day_of_week=self.day_of_week,
            is_active=True,  # فقط با شیفت‌های فعال تداخل را بررسی می‌کنیم
            # تداخل زمانی: شروع شیفت موجود قبل از پایان شیفت جدید
            # و پایان شیفت موجود بعد از شروع شیفت جدید
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)  # خود شیفت جاری را در هنگام ویرایش مستثنی می‌کند

        if conflicting_schedules.exists():
            # می‌توانیم اطلاعات شیفت‌های تداخل‌دار را هم در پیام خطا بدهیم
            raise ValidationError(
                f"این شیفت با یک شیفت فعال موجود برای پزشک {self.doctor.user.get_full_name()} در شعبه {self.location.name} و روز {self.get_day_of_week_display()} تداخل دارد."
            )


# ----------------------------
# ⛔ مدل بلاک زمانی (BlockTime) - نهایی
# ----------------------------
class BlockTime(models.Model):
    """
    ⛔ BlockTime

    این مدل برای تعریف زمان‌های غیرقابل دسترس بودن پزشکان یا منابع طراحی شده است (مانند مرخصی، جلسات، تعمیرات).
    در این بازه‌های زمانی، سیستم نباید اجازه رزرو نوبت را بدهد.
    """
    BLOCK_TYPES = [
        ('doctor_leave', 'مرخصی پزشک'),
        ('meeting', 'جلسه/کنفرانس'),
        ('equipment_maintenance', 'تعمیر تجهیزات'),
        ('other', 'سایر'),
    ]

    name = models.CharField("عنوان بلاک", max_length=255,
                            help_text="عنوان کوتاه برای بلاک زمانی (مثال: مرخصی تابستانی).")
    type = models.CharField("نوع بلاک", max_length=50, choices=BLOCK_TYPES)

    # فیلدهای ارتباطی (یکی یا بیشتر می‌توانند پر شوند)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True,
                               related_name="blocked_times", verbose_name="پزشک مرتبط",
                               help_text="اختیاری: اگر بلاک برای یک پزشک خاص است.")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="blocked_times", verbose_name="منبع مرتبط",
                                 help_text="اختیاری: اگر بلاک برای یک منبع خاص است (مثلاً اتاق، دستگاه).")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name="شعبه مرتبط",
                                 help_text="اختیاری: اگر بلاک برای یک شعبه خاص است (و نه کل سیستم).")

    start_datetime = models.DateTimeField("زمان شروع بلاک")
    end_datetime = models.DateTimeField("زمان پایان بلاک")
    notes = models.TextField("توضیحات تکمیلی", blank=True, null=True)

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "بلاک زمانی"
        verbose_name_plural = "بلاک‌های زمانی"
        ordering = ["start_datetime"]
        indexes = [
            models.Index(fields=['doctor', 'start_datetime', 'end_datetime']),
            models.Index(fields=['resource', 'start_datetime', 'end_datetime']),
            models.Index(fields=['location', 'start_datetime', 'end_datetime']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        target = ""
        if self.doctor:
            target = f"پزشک: {self.doctor.user.get_full_name() if self.doctor.user else self.doctor.medical_code}"
        elif self.resource:
            target = f"منبع: {self.resource.name}"
        elif self.location:
            target = f"شعبه: {self.location.name}"
        else:
            target = "عمومی"

        return f"{self.get_type_display()} ({target}) از {self.start_datetime.strftime('%Y/%m/%d %H:%M')} تا {self.end_datetime.strftime('%Y/%m/%d %H:%M')}"

    def clean(self):
        super().clean()
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("زمان شروع بلاک نمی‌تواند بزرگتر یا مساوی زمان پایان باشد.")

        # 📌 منطق دقیق‌تر برای بررسی تداخل بلاک زمانی
        # اطمینان حاصل می‌کنیم که حداقل یکی از فیلدهای doctor, resource, location پر شده باشد
        if not (self.doctor or self.resource or self.location):
            raise ValidationError("باید حداقل یک پزشک، منبع یا شعبه برای بلاک زمانی مشخص شود.")

        # ساخت یک QuerySet پایه برای بلاک‌های تداخل‌دار
        # (شروع بلاک موجود قبل از پایان بلاک جدید و پایان بلاک موجود بعد از شروع بلاک جدید)
        conflicting_blocks = BlockTime.objects.filter(
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        ).exclude(pk=self.pk)

        # بررسی تداخل بر اساس موجودیت‌های مرتبط
        if self.doctor:
            if conflicting_blocks.filter(doctor=self.doctor).exists():
                raise ValidationError(
                    f"این بلاک زمانی برای پزشک {self.doctor.user.get_full_name() if self.doctor.user else self.doctor.medical_code} با یک بلاک موجود تداخل دارد."
                )
        if self.resource:
            if conflicting_blocks.filter(resource=self.resource).exists():
                raise ValidationError(
                    f"این بلاک زمانی برای منبع {self.resource.name} با یک بلاک موجود تداخل دارد."
                )
        if self.location:
            # اگر بلاک مربوط به شعبه باشد، می‌تواند روی همه پزشکان/منابع آن شعبه تأثیر بگذارد
            # این نیاز به منطق پیچیده‌تری دارد اگر بخواهید BlockTime نوع Location را با BlockTime نوع Doctor/Resource در همان لوکیشن مقایسه کنید.
            # فعلاً فقط تداخل با بلاک‌های دیگر در همان شعبه را بررسی می‌کند.
            if conflicting_blocks.filter(location=self.location).exists():
                raise ValidationError(
                    f"این بلاک زمانی برای شعبه {self.location.name} با یک بلاک موجود تداخل دارد."
                )

        # نکته: اگر یک بلاک "عمومی" (بدون doctor, resource, location) را در نظر بگیریم،
        # باید منطق خاصی برای آن تعریف کنیم (مثلاً بلاک کردن کل سیستم).
