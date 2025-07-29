# accounts/signals.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Role, AccessPermission


@receiver(post_migrate)
def create_super_admin_defaults(sender, **kwargs):
    if sender.name != "accounts":
        return  # جلوگیری از اجرای چندباره برای appهای دیگر
    
    # پرمیژن مخصوص سوپریوزر
    perm, _ = AccessPermission.objects.get_or_create(
        code="superuser",
        defaults={
            "name": "Super User Access",
            "description": "Full access to system (grants is_superuser=True)"
        }
    )

    # نقش admin
    role, _ = Role.objects.get_or_create(
        code="admin",
        defaults={
            "name": "Super Admin",
            "description": "مدیر کل سامانه"
        }
    )
    role.permissions.add(perm)

    # اطلاعات از settings
    phone = getattr(settings, "DEFAULT_SUPERUSER_PHONE", "09100000000")
    password = getattr(settings, "DEFAULT_SUPERUSER_PASSWORD", "admin1234")
    first_name = getattr(settings, "DEFAULT_SUPERUSER_FIRST_NAME", "ادمین")
    last_name = getattr(settings, "DEFAULT_SUPERUSER_LAST_NAME", "سیستم")
    national_code = getattr(settings, "DEFAULT_SUPERUSER_NATIONAL_CODE", "0000000000")

    if not User.objects.filter(username=phone).exists():
        user = User.objects.create_superuser(
            phone_number=phone,
            username=phone,  # اضافه‌شده برای سازگاری با سیستم auth
            password=password,
            first_name=first_name,
            last_name=last_name,
            national_code=national_code,
            role=role
        )
        print(f"✅ سوپر یوزر پیش‌فرض ({phone}) ساخته شد.")
    else:
        print(f"ℹ️ سوپر یوزر ({phone}) از قبل وجود دارد.")
