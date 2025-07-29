from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User


class Command(BaseCommand):
    help = "ایجاد گروه‌ها و سطح دسترسی‌های پیش‌فرض سیستم"

    def handle(self, *args, **kwargs):
        roles = [
            {"name": "admin", "permissions": "__all__"},
            {"name": "doctor", "permissions": [
                "view_user",
                "change_user",
            ]},
            {"name": "staff", "permissions": [
                "view_user",
            ]},
            {"name": "reception", "permissions": [
                "view_user",
            ]},
            {"name": "accounting", "permissions": [
                "view_user",
            ]},
            {"name": "patient", "permissions": []},  # بدون پرمیشن
        ]

        user_ct = ContentType.objects.get_for_model(User)

        for role in roles:
            group, created = Group.objects.get_or_create(name=role["name"])
            if role["permissions"] == "__all__":
                permissions = Permission.objects.filter(content_type=user_ct)
                group.permissions.set(permissions)
            else:
                perm_objs = Permission.objects.filter(
                    codename__in=role["permissions"],
                    content_type=user_ct
                )
                group.permissions.set(perm_objs)

            group.save()
            self.stdout.write(self.style.SUCCESS(f"✅ گروه '{group.name}' آماده است."))
