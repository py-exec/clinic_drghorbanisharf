from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords


# ----------------------------
# تنظیمات ارسال ایمیل (قابل توسعه)
# ----------------------------
class EmailConfig(models.Model):
    PROVIDER_CHOICES = [
        ("SMTP", "SMTP استاندارد"),
        ("SendGrid", "SendGrid"),
        ("Mailgun", "Mailgun"),
        ("AmazonSES", "Amazon SES"),
        ("Other", "سایر"),
    ]

    provider = models.CharField("سرویس‌دهنده", max_length=50, choices=PROVIDER_CHOICES, default="SMTP")
    host = models.CharField("آدرس سرور (Host)", max_length=255)
    port = models.PositiveIntegerField("پورت", default=587)

    username = models.CharField("نام کاربری", max_length=255)
    password = models.CharField("رمز عبور", max_length=255)

    from_email = models.EmailField("آدرس فرستنده", help_text="مثال: no-reply@example.com")

    use_tls = models.BooleanField("TLS فعال باشد؟", default=True)
    use_ssl = models.BooleanField("SSL فعال باشد؟", default=False)

    timeout = models.PositiveIntegerField("زمان انتظار (ثانیه)", default=30)
    is_active = models.BooleanField("فعال؟", default=True)

    description = models.TextField("توضیحات", blank=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "تنظیمات ایمیل"
        verbose_name_plural = "تنظیمات ایمیل"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.provider} | {self.from_email}"

    def display_connection_info(self):
        return f"{self.host}:{self.port} (TLS: {self.use_tls} / SSL: {self.use_ssl})"

    def get_absolute_url(self):
        # فرض بر اینکه یک URL برای ویرایش تنظیمات ایمیل خواهیم داشت
        return reverse('clinic_messenger:email_config_update', kwargs={'pk': self.pk})


# ----------------------------
# قالب‌ (پترن) ایمیل
# ----------------------------
class EmailTemplate(models.Model):
    code = models.CharField("کد قالب", max_length=100, unique=True)
    name = models.CharField("عنوان", max_length=100)
    subject_template = models.CharField("قالب عنوان", max_length=255)
    body_template = models.TextField("قالب متن", help_text="مثلاً: سلام {{ name }}، رمز شما {{ code }} است.")
    config = models.ForeignKey(
        EmailConfig, on_delete=models.CASCADE,
        verbose_name="تنظیمات ارسال",
        related_name="email_templates"
    )
    is_active = models.BooleanField("فعال؟", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "قالب ایمیل"
        verbose_name_plural = "قالب‌های ایمیل"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ----------------------------
# ایمیل ارسالی
# ----------------------------
class EmailMessage(models.Model):
    STATUS_CHOICES = [
        ("pending", "در صف"),
        ("sent", "ارسال شده"),
        ("failed", "ناموفق"),
    ]

    PURPOSE_CHOICES = [
        ("verify", "تأیید ایمیل"),
        ("notify", "اعلان سیستمی"),
        ("marketing", "تبلیغاتی"),
        ("manual", "ارسال دستی"),
    ]

    to_email = models.EmailField("گیرنده")
    subject = models.CharField("موضوع", max_length=255)
    body = models.TextField("متن")

    purpose = models.CharField("نوع ایمیل", max_length=20, choices=PURPOSE_CHOICES, default="manual")
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default="pending")
    response_message = models.TextField("پاسخ سرویس", blank=True)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="ارسال‌کننده",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_emails"
    )

    config = models.ForeignKey(
        EmailConfig,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="تنظیمات ارسال",
        related_name="sent_emails"
    )

    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="قالب استفاده شده",
        related_name="emails"
    )

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "ایمیل"
        verbose_name_plural = "ایمیل‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.to_email} | {self.subject[:40]}"

    @property
    def is_successful(self):
        return self.status == "sent"


# ----------------------------
# تنظیمات سرویس پیامک
# ----------------------------
class SMSConfig(models.Model):
    provider = models.CharField("سرویس‌دهنده", max_length=50, default="IPPanel")
    api_key = models.CharField("کلید API", max_length=255)
    originator = models.CharField("شماره فرستنده", max_length=15)
    is_active = models.BooleanField("فعال؟", default=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "تنظیمات پیامک"
        verbose_name_plural = "تنظیمات پیامک"

    def __str__(self):
        return f"{self.provider} | {self.originator}"

    def get_absolute_url(self):
        return reverse('clinic_messenger:sms_config')  # چون معمولا یک کانفیگ داریم


# ----------------------------
# نوع‌های پترن پیامک
# ----------------------------
class SMSPatternType(models.Model):
    code = models.SlugField("کد یکتا", max_length=50, unique=True)
    title = models.CharField("عنوان", max_length=100)
    description = models.TextField("توضیحات", blank=True)
    is_active = models.BooleanField("فعال؟", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "نوع پترن پیامک"
        verbose_name_plural = "نوع‌های پترن پیامک"
        ordering = ["title"]

    def __str__(self):
        return self.title


# ----------------------------
# پترن پیامک (سازگار با IPPanel)
# ----------------------------
class SMSPattern(models.Model):
    code = models.CharField(
        "کد پترن (از پنل پیامک)",
        max_length=100,
        unique=True,
        help_text="کدی که از IPPanel دریافت می‌کنید، مثل: mhq25jydcgqefq3"
    )

    name = models.CharField(
        "عنوان داخلی",
        max_length=100,
        help_text="مثلاً: احراز هویت، تایید نوبت، یادآوری"
    )

    provider = models.CharField(
        "سرویس‌دهنده",
        max_length=50,
        default="IPPanel",
        help_text="نام سرویس‌دهنده پیامک، مثلاً IPPanel یا Kavenegar"
    )

    body_template = models.TextField(
        "نمایش ساختار پیام (فقط جهت مشاهده)",
        blank=True,
        help_text="فقط برای نمایش ساختار؛ پیام واقعی از طرف پنل ارسال می‌شود"
    )

    config = models.ForeignKey(
        SMSConfig,
        on_delete=models.CASCADE,
        verbose_name="تنظیمات ارسال",
        related_name="patterns"
    )
    type = models.ForeignKey(
        "SMSPatternType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patterns",
        verbose_name="نوع پترن"
    )
    is_active = models.BooleanField("فعال؟", default=True)

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "پترن پیامک"
        verbose_name_plural = "پترن‌های پیامک"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def is_otp_pattern(self):
        return "otp" in self.code.lower() or "otp" in self.name.lower()

    def get_variable_keys(self):
        return list(self.variables.values_list("key", flat=True))

    def get_absolute_url(self):
        # فرض بر اینکه یک URL برای ویرایش پترن خواهیم داشت
        return reverse('clinic_messenger:sms_pattern_update', kwargs={'pk': self.pk})


# ----------------------------
# متغیرهای مرتبط با پترن پیامک
# ----------------------------
class SMSPatternVariable(models.Model):
    DATA_TYPE_CHOICES = [
        ("string", "متن"),
        ("int", "عدد صحیح"),
        ("datetime", "تاریخ/زمان"),
        ("phone", "شماره موبایل"),
    ]

    pattern = models.ForeignKey(
        SMSPattern,
        on_delete=models.CASCADE,
        related_name="variables",
        verbose_name="پترن مرتبط"
    )

    key = models.CharField("نام متغیر", max_length=50)  # مثل code, name, date
    label = models.CharField("عنوان نمایشی", max_length=100)
    data_type = models.CharField("نوع داده", max_length=20, choices=DATA_TYPE_CHOICES, default="string")
    required = models.BooleanField("اجباری است؟", default=True)
    hint = models.CharField("توضیح برای فرم یا اپراتور", max_length=200, blank=True)

    class Meta:
        unique_together = ("pattern", "key")
        verbose_name = "متغیر پترن پیامک"
        verbose_name_plural = "متغیرهای پترن پیامک"

    def __str__(self):
        return f"{self.pattern.name} | {self.key} → {selflabel}"


# ----------------------------
# پیامک ارسالی
# ----------------------------
class SMSMessage(models.Model):
    STATUS_CHOICES = [
        ("pending", "در صف"),
        ("sent", "ارسال شده"),
        ("failed", "ناموفق"),
    ]

    PURPOSE_CHOICES = [
        ("otp", "کد تایید"),
        ("notify", "اطلاع‌رسانی"),
        ("marketing", "تبلیغاتی"),
        ("manual", "دستی"),
    ]

    to = models.CharField("شماره گیرنده", max_length=15)
    body = models.TextField("متن پیام")
    purpose = models.CharField("نوع پیام", max_length=20, choices=PURPOSE_CHOICES, default="manual")
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default="pending")
    response_message = models.TextField("پاسخ سرویس", blank=True)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ارسال‌کننده",
        related_name="sent_sms"
    )

    config = models.ForeignKey(
        SMSConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تنظیم ارسال",
        related_name="sent_messages"
    )

    pattern = models.ForeignKey(
        SMSPattern,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پترن استفاده شده",
        related_name="messages"
    )

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "پیامک"
        verbose_name_plural = "پیامک‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.to} | {self.purpose} | {self.body[:30]}..."

    @property
    def is_successful(self):
        return self.status == "sent"


# ----------------------------
# کد تأیید (OTP)
# ----------------------------
class OTPCode(models.Model):
    PURPOSE_CHOICES = [
        ("verify", "تأیید شماره موبایل"),
        ("login", "ورود با موبایل"),
        ("reset", "فراموشی رمز عبور"),
        ("2fa", "ورود دو مرحله‌ای"),
    ]

    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("sent", "ارسال شده"),
        ("expired", "منقضی شده"),
        ("verified", "تأیید شده"),
        ("failed", "ناموفق"),
    ]

    phone_number = models.CharField("شماره موبایل", max_length=15)
    code = models.CharField("کد تأیید", max_length=10)
    purpose = models.CharField("کاربرد", max_length=10, choices=PURPOSE_CHOICES)
    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default="pending")
    is_verified = models.BooleanField("تأیید شده", default=False)

    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    expires_at = models.DateTimeField("زمان انقضا")

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="کاربر درخواست‌دهنده",
        related_name="otp_requests"
    )

    config = models.ForeignKey(
        SMSConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تنظیم ارسال پیامک",
        related_name="otp_codes"
    )

    sms_message = models.OneToOneField(
        SMSMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پیامک مربوطه",
        related_name="otp_code"
    )

# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "کد OTP"
        verbose_name_plural = "کدهای OTP"
        indexes = [models.Index(fields=["phone_number", "code"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone_number} | {self.purpose} | {self.code} | {self.status}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_expired(self):
        self.status = "expired"
        self.save(update_fields=["status"])
