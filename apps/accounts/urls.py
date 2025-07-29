# apps/accounts/urls.py

from django.urls import path

from . import views, views_acl, views_otp

app_name = "accounts"

urlpatterns = [
    # ------------------ احراز هویت و پروفایل کاربر ------------------
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),

    # OTP (رمز یکبار مصرف)
    path("send-otp/", views_otp.send_otp_view, name="send-otp"),
    path("verify-otp/", views_otp.verify_otp_view, name="verify-otp"),

    # ------------------ مدیریت کاربران (Users) ------------------
    # URL اصلی منو: 'accounts:user-list'
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/create/", views.UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/update/", views.UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", views.UserSoftDeleteView.as_view(), name="user-delete"),

    # ------------------ مدیریت نقش‌ها (Roles) ------------------
    # URL اصلی منو: 'accounts:role-list'
    path("roles/", views_acl.RoleListView.as_view(), name="role-list"),
    path("roles/create/", views_acl.RoleCreateView.as_view(), name="role-create"),
    path("roles/<int:pk>/", views_acl.RoleDetailView.as_view(), name="role-detail"),
    path("roles/<int:pk>/update/", views_acl.RoleUpdateView.as_view(), name="role-update"),
    path("roles/<int:pk>/delete/", views_acl.RoleDeleteView.as_view(), name="role-delete"),

    # ------------------ مدیریت مجوزها (Permissions) ------------------
    # URL اصلی منو: 'accounts:permission-list'
    path("permissions/", views_acl.PermissionListView.as_view(), name="permission-list"),
    path("permissions/create/", views_acl.PermissionCreateView.as_view(), name="permission-create"),
    path("permissions/<int:pk>/", views_acl.PermissionDetailView.as_view(), name="permission-detail"),
    path("permissions/<int:pk>/update/", views_acl.PermissionUpdateView.as_view(), name="permission-update"),
    path("permissions/<int:pk>/delete/", views_acl.PermissionDeleteView.as_view(), name="permission-delete"),
]
