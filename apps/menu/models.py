# apps/menu/models.py

import json  # 👈 جدید: برای کار با JSONField
# ایمپورت مدل‌های AccessPermission و Role از اپ accounts.
from apps.accounts.models import AccessPermission, Role
from django.conf import settings
from django.contrib.postgres.fields import ArrayField  # برای فیلد highlight_url_names
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class MenuItem(models.Model):
    """
    📦 MenuItem – مدل پیشرفته برای ساختار منوهای داینامیک و سلسله‌مراتبی.

    این مدل تمامی جنبه‌های یک آیتم منو را پوشش می‌دهد:
    - ساختار درختی (والد و فرزندان) برای منوهای تودرتو.
    - انواع آیتم (لینک، عنوان بخش، جداکننده) برای انعطاف‌پذیری در طراحی منو.
    - انواع مقصد لینک (URL نام‌گذاری شده Django، مسیر ثابت، URL خارجی)
      برای هدایت کاربران به صفحات مختلف.
    - کنترل دسترسی (ACL) بر اساس مجوزها و نقش‌های کاربر برای شخصی‌سازی منو.
    - هایلایت هوشمند آیتم منوی فعال بر اساس URL فعلی کاربر.
    - ردیابی تاریخچه تغییرات با Simple History.
    - مدیریت وضعیت (فعال/غیرفعال، نمایش در منو، تولید خودکار).
    - اعتبارسنجی برای جلوگیری از حلقه‌های بی‌پایان در ساختار درختی منو.
    - پشتیبانی از URLهای پارامتریک (جدید).
    """

    class ItemType(models.TextChoices):
        """انواع مختلف آیتم‌های منو."""
        LINK = "link", _("لینک (صفحه)")  # 👈 EXTERNAL_LINK از اینجا حذف شد و توسط LINK + LinkType.EXTERNAL هندل می‌شود.
        HEADER = "header", _("عنوان گروه (Header)")
        DIVIDER = "divider", _("جداکننده (Divider)")

    class LinkType(models.TextChoices):
        """نحوه تفسیر `link_target`."""
        REVERSE = "reverse", _("نام URL (Django)")
        STATIC = "static", _("لینک ثابت (مسیر مطلق)")
        EXTERNAL = "external", _("لینک خارجی (URL کامل)")

        # --- اطلاعات نمایشی و محتوایی ---

    title = models.CharField(
        _("عنوان منو"), max_length=150,
        help_text=_("عنوان قابل نمایش آیتم در منو. (مثلاً: 'داشبورد', 'لیست بیماران').")
    )
    description = models.TextField(
        _("توضیحات"), blank=True, null=True,
        help_text=_("توضیحات کوتاه یا tooltip برای آیتم منو.")
    )

    item_type = models.CharField(
        _("نوع آیتم"), max_length=20, choices=ItemType.choices, default=ItemType.LINK,
        help_text=_("نوع آیتم منو را مشخص می‌کند (مثلاً: لینک به یک صفحه، عنوان یک گروه، یا خط جداکننده).")
    )

    # --- تنظیمات لینک‌دهی ---
    link_type = models.CharField(
        _("نوع لینک"), max_length=10, choices=LinkType.choices, default=LinkType.REVERSE,
        help_text=_("نحوه تفسیر 'مقصد لینک'. (مثلاً: آیا 'dashboard' یک نام URL است یا یک مسیر ثابت).")
    )
    link_target = models.CharField(
        _("مقصد لینک"), max_length=500, blank=True, null=True,
        help_text=_(
            "مقدار لینک. بر اساس 'نوع لینک' می‌تواند یک نام URL جنگو، یک مسیر ثابت، یا یک URL خارجی باشد. (مثلاً: 'dashboard' یا '/about/' یا 'https://example.com').")
    )

    # 📌 جدید: برای URLهای پارامتریک (reverse با آرگومان)
    reverse_args_json = models.JSONField(
        _("آرگومان‌های URL (JSON)"), blank=True, null=True,
        help_text=_("آرگومان‌های positional برای reverse کردن URL (مثلاً: [1, 'detail']). باید JSON معتبر باشد.")
    )
    reverse_kwargs_json = models.JSONField(
        _("آرگومان‌های کلیدواژه URL (JSON)"), blank=True, null=True,
        help_text=_("آرگومان‌های keyword برای reverse کردن URL (مثلاً: {'pk': 1}). باید JSON معتبر باشد.")
    )

    highlight_url_names = ArrayField(
        base_field=models.CharField(max_length=100),
        blank=True,
        null=True,
        verbose_name=_("URL های مرتبط برای هایلایت"),
        help_text=_(
            "لیستی از نام‌های URL (جنگو) که در صورت فعال بودن مسیر آن‌ها، این آیتم منو هایلایت شود. (مثال: ['patient:detail', 'patient:edit']).")
    )

    # --- ساختار سلسله‌مراتبی (منوهای تو در تو) ---
    parent = models.ForeignKey(
        "self", verbose_name=_("والد (منوی بالاتر)"),
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name="children",
        help_text=_("اگر این آیتم زیرمنوی یک آیتم دیگر است، والد آن را انتخاب کنید. (برای ساخت منوهای درختی).")
    )
    order = models.PositiveIntegerField(
        _("ترتیب نمایش"), default=0,
        help_text=_("ترتیب نمایش آیتم در بین آیتم‌های هم‌سطح (والد یکسان).")
    )

    # --- تنظیمات ظاهری ---
    icon = models.CharField(
        _("کلاس آیکون"), max_length=100, default="bx-circle",
        help_text=_("کلاس CSS برای آیکون آیتم منو. (مثلاً: 'bx bx-home', 'tf-icons bx bx-group').")
    )
    badge = models.CharField(
        _("نشان (Badge)"), max_length=20, blank=True, null=True,
        help_text=_("متن نشان کوچک کنار آیتم منو (مثلاً: 'جدید', '۴', 'بتا').")
    )
    css_class = models.CharField(
        _("کلاس CSS سفارشی"), max_length=100, blank=True, null=True,
        help_text=_("کلاس CSS اضافی برای استایل‌دهی سفارشی این آیتم منو.")
    )

    # --- وضعیت و کنترل ---
    show_in_menu = models.BooleanField(
        _("نمایش در منو"), default=True,
        help_text=_("آیا این آیتم باید در منوی اصلی ناوبری (UI) نمایش داده شود؟")
    )
    is_active = models.BooleanField(
        _("فعال؟"), default=True,
        help_text=_("آیا این آیتم منو در حال حاضر فعال است و قابل استفاده است؟ (غیرفعال کردن آن را پنهان می‌کند).")
    )
    auto_generated = models.BooleanField(
        _("تولید خودکار؟"), default=False,
        help_text=_("آیا این آیتم منو به صورت خودکار توسط سیستم تولید شده است؟ (برای جلوگیری از تغییرات دستی).")
    )

    # --- کنترل دسترسی (ACL) ---
    permissions = models.ManyToManyField(
        AccessPermission, blank=True,
        related_name="menu_items", verbose_name=_("مجوزهای لازم"),
        help_text=_(
            "مجوزهای AccessPermission که کاربر برای دیدن این آیتم منو باید داشته باشد. (کاربر باید حداقل یکی را داشته باشد).")
    )
    required_roles = models.ManyToManyField(
        Role, blank=True,
        related_name="menu_items_by_role", verbose_name=_("نقش‌های لازم"),
        help_text=_(
            "نقش‌های (Role) که کاربر برای دیدن این آیتم منو باید داشته باشد. (کاربر باید حداقل یکی را داشته باشد).")
    )

    # --- تاریخچه و متادیتا ---
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخرین بروزرسانی"), auto_now=True)
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()  # برای ردیابی تاریخچه تغییرات مدل

    class Meta:
        verbose_name = _("آیتم منو")
        verbose_name_plural = _("منوها")
        ordering = ["parent__id", "order", "title"]
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['is_active', 'show_in_menu']),
            models.Index(fields=['item_type']),
            models.Index(fields=['link_type']),
        ]

    def __str__(self):
        """
        نمایش عنوان و نوع آیتم منو برای خوانایی بهتر در پنل ادمین.
        """
        return f"{self.title} ({self.get_item_type_display()})"

    def resolve_url(self):
        """
        URL واقعی آیتم منو را بر اساس `item_type`, `link_type`, و `link_target` بازمی‌گرداند.
        در صورت عدم یافتن URL، None برگردانده می‌شود.
        """
        # آیتم‌های از نوع HEADER یا DIVIDER فاقد URL هستند.
        if self.item_type in [self.ItemType.HEADER, self.ItemType.DIVIDER]:
            return None

        if self.link_type == self.LinkType.REVERSE and self.link_target:
            args = self.reverse_args_json if self.reverse_args_json else []
            kwargs = self.reverse_kwargs_json if self.reverse_kwargs_json else {}
            try:
                # تلاش برای reverse کردن نام URL جنگو با آرگومان‌ها.
                return reverse(self.link_target, args=args, kwargs=kwargs)
            except NoReverseMatch:
                # اگر نام URL پیدا نشد، یا نیاز به آرگومان داشت، None برگردانده می‌شود.
                # می‌توانید این خطا را لاگ کنید تا مشکلات پیکربندی شناسایی شوند.
                return None

        if self.link_type == self.LinkType.STATIC and self.link_target:
            # بازگرداندن یک مسیر ثابت داخلی.
            return self.link_target

        if self.link_type == self.LinkType.EXTERNAL and self.link_target:
            # بازگرداندن یک URL خارجی کامل.
            return self.link_target

            # اگر item_type لینک است اما link_target خالی است یا link_type نامعتبر است.
        return None  # 👈 اصلاح: بازگشت None به جای "#"

    def has_access(self, user):
        """
        بررسی می‌کند که آیا کاربر فعلی به این آیتم منو دسترسی دارد.
        این تابع تمامی قواعد ACL و نمایش را در نظر می‌گیرد.
        """

        if not self.is_active or not self.show_in_menu:
            return False

        if user.is_superuser:
            return True

        if self.item_type in [self.ItemType.HEADER, self.ItemType.DIVIDER]:
            return any(child.has_access(user) for child in self.children.all())

        if self.permissions.exists() or self.required_roles.exists():
            if not user.is_authenticated:
                return False

            if self.required_roles.exists():
                if not hasattr(user, 'role') or not user.role:
                    return False
                if not self.required_roles.filter(id=user.role.id).exists():
                    return False

            if self.permissions.exists():
                user_perms_codes = user.get_permissions()
                if not self.permissions.filter(code__in=user_perms_codes).exists():
                    return False

        return True

    def clean(self):
        """
        متد clean() برای اعتبارسنجی‌های سفارشی مدل.
        این متد برای جلوگیری از حلقه‌های بی‌پایان در ساختار درختی منو استفاده می‌شود.
        """
        super().clean()

        # 1. اعتبارسنجی: آیتم‌های از نوع 'HEADER' یا 'DIVIDER' نباید لینک داشته باشند.
        if self.item_type in [self.ItemType.HEADER, self.ItemType.DIVIDER]:
            if self.link_target:
                raise ValidationError(
                    _("آیتم‌های از نوع 'عنوان بخش' یا 'جداکننده' نباید مقصد لینک داشته باشند.")
                )
            self.link_type = self.LinkType.STATIC  # تنظیم به یک مقدار پیش‌فرض معتبر.
            self.link_target = None

        # 2. اعتبارسنجی: آیتم‌های از نوع 'LINK' باید link_target داشته باشند.
        # 👈 اصلاح: اکنون item_type.LINK هم می‌تواند لینک خارجی باشد.
        elif self.item_type == self.ItemType.LINK and not self.link_target:
            raise ValidationError(_("آیتم‌های از نوع لینک باید مقصد لینک (link_target) داشته باشند."))

        # 3. اعتبارسنجی: نوع لینک باید با نوع آیتم همخوانی داشته باشد.
        # 👈 اصلاح: item_type.LINK اکنون می‌تواند با LinkType.EXTERNAL هم استفاده شود.
        if self.item_type == self.ItemType.LINK:
            if self.link_type not in [self.LinkType.REVERSE, self.LinkType.STATIC, self.LinkType.EXTERNAL]:
                raise ValidationError(
                    _("آیتم‌های از نوع 'لینک' باید نوع لینک 'نام URL (Django)', 'لینک ثابت' یا 'لینک خارجی' داشته باشند."))

        # 4. 👈 جدید: اعتبارسنجی برای فیلدهای reverse_args_json و reverse_kwargs_json
        if self.link_type == self.LinkType.REVERSE:
            if self.reverse_args_json is not None and not isinstance(self.reverse_args_json, list):
                raise ValidationError(_("آرگومان‌های positional برای reverse باید یک لیست (JSON Array) باشند."))
            if self.reverse_kwargs_json is not None and not isinstance(self.reverse_kwargs_json, dict):
                raise ValidationError(_("آرگومان‌های کلیدواژه برای reverse باید یک دیکشنری (JSON Object) باشند."))
        else:  # اگر link_type از نوع REVERSE نیست، این فیلدها باید خالی باشند.
            if self.reverse_args_json is not None or self.reverse_kwargs_json is not None:
                raise ValidationError(_("آرگومان‌های reverse فقط برای نوع لینک 'نام URL (Django)' قابل استفاده هستند."))

        # 5. اعتبارسنجی برای جلوگیری از حلقه‌های بی‌پایان (Circular Parent-Child Relationships)
        if self.parent:  # اگر والد انتخاب شده است
            current_parent = self.parent
            visited_parents = {self.pk}  # شروع با ID خود آیتم برای جلوگیری از Self-referencing loop

            while current_parent:
                if current_parent.pk in visited_parents:
                    raise ValidationError(
                        _("ایجاد حلقه در ساختار منو: این آیتم نمی‌تواند فرزند این والد باشد زیرا باعث ایجاد حلقه می‌شود. لطفاً والد دیگری را انتخاب کنید.")
                    )
                visited_parents.add(current_parent.pk)
                current_parent = current_parent.parent  # حرکت به والد بعدی در سلسله‌مراتب

    def save(self, *args, **kwargs):
        """
        متد save() را برای اعمال اعتبارسنجی‌های اضافی و تنظیمات پیش از ذخیره override می‌کنیم.
        متد clean() قبل از save() در فرم‌ها فراخوانی می‌شود، اما برای اطمینان، full_clean()
        را در ابتدای save() فراخوانی می‌کنیم تا تمام اعتبارسنجی‌ها اجرا شوند.
        """
        try:
            self.full_clean()  # فراخوانی clean() برای اجرای تمام اعتبارسنجی‌ها قبل از ذخیره
        except ValidationError as e:
            raise e  # اگر اعتبارسنجی full_clean با خطا مواجه شد، آن را مجدداً بالا می‌اندازیم.

        super().save(*args, **kwargs)
