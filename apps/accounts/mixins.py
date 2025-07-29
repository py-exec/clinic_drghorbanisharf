from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


# ----------------------------
# میکسین کنترل بر اساس نقش
# ----------------------------
class RoleRequiredMixin(UserPassesTestMixin):
    """
    بررسی می‌کند که کاربر نقش مشخص‌شده‌ای دارد یا نه.
    استفاده: required_roles = ["admin", "doctor"]
    """

    required_roles = []

    def test_func(self):
        user = self.request.user
        if not self.request.user.is_authenticated:
            return False

        if user.is_superuser:
            return True  # سوپر یوزر همیشه مجازه

        user_role = getattr(self.request.user.role, "code", None)
        return user_role in self.required_roles

    def handle_no_permission(self):
        raise PermissionDenied(_("⛔ دسترسی غیرمجاز: نقش شما مجاز نیست."))


# ----------------------------
# میکسین کنترل بر اساس Permission
# ----------------------------
class PermissionRequiredMixin(UserPassesTestMixin):
    """
    بررسی می‌کند که کاربر دسترسی ACL مشخصی دارد یا نه.
    استفاده: required_permissions = ["view_user", "delete_doctor"]
    """

    required_permissions = []

    def test_func(self):
        user = self.request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True  # سوپر یوزر همیشه مجازه

        return all(user.has_permission(code) for code in self.required_permissions)

    def handle_no_permission(self):
        raise PermissionDenied(_("⛔ دسترسی غیرمجاز: شما این مجوز را ندارید."))
