from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords

from .managers import CustomUserManager

USER_LEVEL_CHOICES = [
    ("normal", "عمومی"),
    ("cip", "CIP - خدمات ویژه"),
    ("vip", "VIP - بیمار خاص"),
    ("referral", "ارجاعی"),
    ("special", "خدمات خاص / خیرین"),
]


# ----------------------------
# 📦 مدل دسترسی سفارشی (برای ACL)
# ----------------------------
class AccessPermission(models.Model):
    """
    📦 AccessPermission

    این مدل برای تعریف مجوزها و دسترسی‌های سیستم طراحی شده است.
    هر مجوز شامل یک کد یکتا و نام نمایشی است که می‌تواند به نقش‌ها (Role) مرتبط شود.

    ویژگی‌ها:
    - name: نام نمایشی دسترسی (برای نمایش در پنل‌ها یا لاگ‌ها).
    - code: کد یکتا (slug) که به‌عنوان شناسه دسترسی در سیستم استفاده می‌شود.
      (مثال: view_user، edit_staff)
    - description: توضیحات اختیاری برای تشریح کاربرد دسترسی.

    متا:
    - مرتب‌سازی: بر اساس code
    - نام‌های فارسی برای مدیریت ادمین.

    """
    name = models.CharField("نام نمایشی", max_length=100)
    code = models.SlugField("کد دسترسی", max_length=50, unique=True,
                            help_text="مثال: view_user، edit_staff، delete_report")
    description = models.TextField("توضیحات", blank=True)

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "دسترسی"
        verbose_name_plural = "دسترسی‌ها"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse('accounts:permission-detail', kwargs={'pk': self.pk})


# ----------------------------
# 👥 مدل نقش‌های داینامیک
# ----------------------------
class Role(models.Model):
    """
    👥 Role

    این مدل نقش‌های مختلف سیستم را مدیریت می‌کند. هر نقش می‌تواند مجموعه‌ای از مجوزها (AccessPermission)
    را داشته باشد و در کنترل دسترسی ACL برای کاربران استفاده می‌شود.

    ویژگی‌ها:
    - name: نام نقش (مانند: مدیر، پزشک، کارمند)
    - code: کد یکتا (slug) نقش (مانند: admin, doctor, staff)
    - description: توضیحات اختیاری برای شرح نقش.
    - permissions: مجوزهای مرتبط با این نقش (ManyToMany با AccessPermission)

    متا:
    - مرتب‌سازی: بر اساس name
    - نام‌های فارسی برای مدیریت ادمین.

    """
    name = models.CharField("نام نقش", max_length=100, unique=True)
    code = models.SlugField("کد نقش", max_length=50, unique=True, help_text="مثال: admin, doctor, staff")
    description = models.TextField("توضیحات", blank=True)

    permissions = models.ManyToManyField(
        AccessPermission,
        related_name="roles",
        verbose_name="دسترسی‌های این نقش",
        blank=True
    )

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "نقش"
        verbose_name_plural = "نقش‌ها"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse('accounts:role-detail', kwargs={'pk': self.pk})


# ----------------------------
# 👤 مدل کاربر سفارشی
# ----------------------------
class User(AbstractUser):
    """
    📦 مدل کاربر سفارشی سیستم

    این مدل به عنوان جایگزین مدل پیش‌فرض Django عمل می‌کند و شامل اطلاعات فردی، ACL (دسترسی و نقش‌ها)،
    تاریخچه فعالیت، و سایر ویژگی‌های مرتبط با کاربر است.

    ویژگی‌ها:
    - اطلاعات فردی: نام، نام خانوادگی، کد ملی (ملی)، شماره موبایل (به‌عنوان فیلد اصلی ورود)، ایمیل و تصویر پروفایل.
    - نقش (Role) و وضعیت‌های تأیید (is_verified, phone_verified, email_verified).
    - تاریخچه فعالیت (last_seen, ip_address) و اطلاعات ثبت و بروزرسانی.
    - ACL: نقش مرتبط و مجوزهای اختصاصی به آن.
    - پشتیبانی از "soft delete" (غیرفعال کردن به‌جای حذف واقعی).

    متدهای کلیدی:
    - save(): تنظیم خودکار نام‌کاربری (username) بر اساس شماره موبایل.
    - soft_delete(): غیرفعال‌سازی کاربر به‌جای حذف.
    - update_last_seen(request): بروزرسانی تاریخچه فعالیت و IP.
    - has_permission(code): بررسی مجوز خاص بر اساس نقش مرتبط.
    - get_permissions(): دریافت لیست کدهای دسترسی.
    - has_role(code): بررسی نقش خاص.

    🛠️ پیش‌فرض‌ها:
    - USERNAME_FIELD: phone_number
    - REQUIRED_FIELDS: first_name, last_name, national_code

    ✍️ نکات:
    - ACL به‌طور کامل توسط Role و AccessPermission کنترل می‌شود.
    - اطمینان حاصل شود که نقش‌ها و دسترسی‌ها به‌درستی تعریف و تنظیم شده‌اند.

    """

    objects = CustomUserManager()

    # اطلاعات فردی
    first_name = models.CharField("نام", max_length=50)
    last_name = models.CharField("نام خانوادگی", max_length=50)
    nickname = models.CharField("نام مستعار", max_length=50, blank=True, null=True, unique=True)
    national_code = models.CharField("کد ملی", max_length=10, unique=True, db_index=True)
    GENDER_CHOICES = (
        ('male', 'مرد'),
        ('female', 'زن'),
        ('other', 'سایر'),
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="جنسیت"
    )
    birth_date = models.DateField("تاریخ تولد", null=True, blank=True)
    phone_number = models.CharField("شماره موبایل", max_length=15, unique=True, db_index=True)
    email = models.EmailField("ایمیل", blank=True, null=True)
    profile_image = models.ImageField("تصویر پروفایل", upload_to="users/profile/", blank=True, null=True)
    MARRIAGE_CHOICES = (
        ('single', 'مجرد'),
        ('married', 'متاهل'),
        ('other', 'سایر'),
    )
    service_level = models.CharField(max_length=20, choices=USER_LEVEL_CHOICES, default="normal",
                                     verbose_name="سطح کاربر")
    marriage = models.CharField(
        max_length=20,
        choices=MARRIAGE_CHOICES,
        blank=True,
        null=True,
        verbose_name="وضعیت تأهل"
    )
    language = models.CharField("زبان", max_length=10, choices=[('fa', 'فارسی'), ('en', 'English')], default='fa')
    nationality = models.CharField("ملیت", max_length=50, blank=True, null=True)
    bio = models.TextField("بیوگرافی", blank=True, null=True)

    # نقش و وضعیت
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        null=True,
        related_name="users",
        verbose_name="نقش"
    )
    is_verified = models.BooleanField("تأیید شده توسط ادمین", default=False)
    is_active = models.BooleanField("فعال", default=True)
    phone_verified = models.BooleanField("موبایل تأیید شده", default=False)
    email_verified = models.BooleanField("ایمیل تأیید شده", default=False)

    # امنیت و لاگ
    last_seen = models.DateTimeField("آخرین فعالیت", null=True, blank=True)
    ip_address = models.GenericIPAddressField("آخرین IP", null=True, blank=True)
    last_password_change = models.DateTimeField("آخرین تغییر رمز", null=True, blank=True)

    # متا
    created_by = models.ForeignKey(
        "self",
        verbose_name="ایجاد شده توسط",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users"
    )
    date_joined = models.DateTimeField("تاریخ ثبت‌نام", default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    # تاریخچه
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name", "last_name", "national_code"]

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.phone_number and not self.username:
            self.username = self.phone_number
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def update_last_seen(self, request):
        self.last_seen = timezone.now()
        self.ip_address = request.META.get("REMOTE_ADDR")
        self.save(update_fields=["last_seen", "ip_address"])

    def has_permission(self, code: str) -> bool:
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(code=code).exists()

    def get_permissions(self):
        if self.is_superuser:
            return AccessPermission.objects.all().values_list("code", flat=True)
        if not self.role:
            return []
        return list(self.role.permissions.values_list("code", flat=True))

    def has_role(self, role_code: str) -> bool:
        return self.role and self.role.code == role_code

    def get_absolute_url(self):
        return reverse('accounts:user-detail', kwargs={'pk': self.pk})

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                    (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    @property
    def full_address(self):
        return f"{self.get_full_name()}، {self.address or 'نامشخص'}"


# ----------------------------
# 📞 مدل شماره‌های تماس کاربر
# ----------------------------
class UserPhone(models.Model):
    PHONE_TYPE_CHOICES = [
        ('mobile', 'موبایل'),
        ('home', 'منزل'),
        ('office', 'دفتر'),
        ('other', 'سایر')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    phone_number = models.CharField(max_length=15, verbose_name="شماره تماس")
    label = models.CharField(max_length=20, choices=PHONE_TYPE_CHOICES, default='mobile', verbose_name="نوع شماره")
    is_primary = models.BooleanField(default=False, verbose_name="شماره اصلی")
    is_verified = models.BooleanField(default=False, verbose_name="تأیید شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    def __str__(self):
        return f"{self.phone_number} ({self.label})"


# ----------------------------
# 🏠 مدل آدرس‌های کاربر
# ----------------------------
class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='home', verbose_name="برچسب")
    state = models.CharField(max_length=50, verbose_name="استان")
    city = models.CharField(max_length=50, verbose_name="شهر")
    street = models.TextField(verbose_name="خیابان")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="کد پستی")
    is_default_shipping = models.BooleanField(default=False, verbose_name="آدرس پیش‌فرض ارسال")
    is_default_billing = models.BooleanField(default=False, verbose_name="آدرس پیش‌فرض مالی")
    is_verified = models.BooleanField(default=False, verbose_name="تأیید شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    def __str__(self):
        return f"{self.label} - {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default_shipping:
            UserAddress.objects.filter(user=self.user, is_default_shipping=True).exclude(pk=self.pk).update(
                is_default_shipping=False)
        if self.is_default_billing:
            UserAddress.objects.filter(user=self.user, is_default_billing=True).exclude(pk=self.pk).update(
                is_default_billing=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.postal_code and not re.match(r'^\d{10}$', self.postal_code):
            raise ValidationError("کد پستی باید ۱۰ رقمی باشد.")


class OTPCode(models.Model):
    PURPOSE_CHOICES = [
        ("verify", "تأیید شماره"),
        ("login", "ورود بدون رمز"),
        ("reset", "بازیابی رمز"),
        ("2fa", "ورود دو مرحله‌ای"),
    ]

    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone_number} - {self.purpose} - {self.code}"
