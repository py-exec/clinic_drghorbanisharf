# apps/accounts/views_acl.py

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import RoleForm, AccessPermissionForm
from .models import Role, AccessPermission


# ----------------------------
# مدیریت نقش‌ها (Roles)
# ----------------------------
class RoleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Role
    template_name = "accounts/acl/role_list.html"
    context_object_name = "roles"
    permission_required = "accounts.view_role"


class RoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = "accounts/acl/role_form.html"
    permission_required = "accounts.add_role"
    success_url = reverse_lazy("accounts:role-list")

    def form_valid(self, form):
        messages.success(self.request, "نقش جدید با موفقیت ساخته شد.")
        return super().form_valid(form)


class RoleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = "accounts/acl/role_form.html"
    permission_required = "accounts.change_role"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "نقش با موفقیت ویرایش شد.")
        return super().form_valid(form)


class RoleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Role
    template_name = "accounts/acl/role_confirm_delete.html"
    permission_required = "accounts.delete_role"
    success_url = reverse_lazy("accounts:role-list")

    def form_valid(self, form):
        messages.warning(self.request, f"نقش '{self.object.name}' با موفقیت حذف شد.")
        return super().form_valid(form)


class RoleDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Role
    template_name = "accounts/acl/role_detail.html"
    context_object_name = "role"
    permission_required = "accounts.view_role"


# ----------------------------
# مدیریت مجوزها (Permissions)
# ----------------------------
class PermissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AccessPermission
    template_name = "accounts/acl/permission_list.html"
    context_object_name = "permissions"
    permission_required = "accounts.view_accesspermission"


class PermissionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AccessPermission
    form_class = AccessPermissionForm
    template_name = "accounts/acl/permission_form.html"
    permission_required = "accounts.add_accesspermission"
    success_url = reverse_lazy("accounts:permission-list")

    def form_valid(self, form):
        messages.success(self.request, "مجوز جدید با موفقیت ایجاد شد.")
        return super().form_valid(form)


class PermissionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AccessPermission
    form_class = AccessPermissionForm
    template_name = "accounts/acl/permission_form.html"
    permission_required = "accounts.change_accesspermission"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "مجوز با موفقیت ویرایش شد.")
        return super().form_valid(form)


class PermissionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AccessPermission
    template_name = "accounts/acl/permission_confirm_delete.html"
    permission_required = "accounts.delete_accesspermission"
    success_url = reverse_lazy("accounts:permission-list")

    def form_valid(self, form):
        messages.warning(self.request, f"مجوز '{self.object.name}' با موفقیت حذف شد.")
        return super().form_valid(form)


class PermissionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = AccessPermission
    template_name = "accounts/acl/permission_detail.html"
    context_object_name = "permission"
    permission_required = "accounts.view_accesspermission"
