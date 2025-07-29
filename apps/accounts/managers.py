from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    مدیر کاربر سفارشی برای استفاده از شماره موبایل به‌جای نام کاربری.
    """

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_("شماره موبایل الزامی است."))

        # اطمینان از وجود فیلد username برای سازگاری با AbstractUser
        extra_fields.setdefault("username", phone_number)

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        # تنظیم پیش‌فرض‌ها برای سوپریوزر
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        # اعتبارسنجی
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("سوپریوزر باید دسترسی ادمین داشته باشد (is_staff=True)."))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("سوپریوزر باید دسترسی کامل داشته باشد (is_superuser=True)."))

        if not password:
            raise ValueError(_("رمز عبور برای سوپریوزر الزامی است."))

        # اطمینان از وجود username برای AbstractUser
        extra_fields.setdefault("username", phone_number)

        return self.create_user(phone_number, password, **extra_fields)
