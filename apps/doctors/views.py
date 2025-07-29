from apps.accounts.mixins import RoleRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import DoctorForm, SpecialtyForm, SpecialtyCategoryForm
from .models import Doctor, Specialty, SpecialtyCategory


# ----------------------------
# دسته‌بندی تخصص‌ها
# ----------------------------
@method_decorator(login_required, name='dispatch')
class SpecialtyCategoryListView(RoleRequiredMixin, ListView):
    model = SpecialtyCategory
    template_name = "doctors/specialty_category_list.html"
    context_object_name = "categories"
    required_roles = ["admin", "hr"]


@method_decorator(login_required, name='dispatch')
class SpecialtyCategoryCreateView(RoleRequiredMixin, CreateView):
    model = SpecialtyCategory
    form_class = SpecialtyCategoryForm
    template_name = "doctors/specialty_category_form.html"
    success_url = reverse_lazy("doctors:specialty-category-list")
    required_roles = ["admin"]

    def form_valid(self, form):
        messages.success(self.request, "✅ دسته تخصص جدید با موفقیت ایجاد شد.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class SpecialtyCategoryUpdateView(RoleRequiredMixin, UpdateView):
    model = SpecialtyCategory
    form_class = SpecialtyCategoryForm
    template_name = "doctors/specialty_category_form.html"
    success_url = reverse_lazy("doctors:specialty-category-list")
    required_roles = ["admin"]

    def form_valid(self, form):
        messages.success(self.request, "✅ دسته تخصص بروزرسانی شد.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class SpecialtyCategoryDeleteView(RoleRequiredMixin, DeleteView):
    model = SpecialtyCategory
    template_name = "doctors/specialty_category_confirm_delete.html"
    success_url = reverse_lazy("doctors:specialty-category-list")
    required_roles = ["admin"]

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "❌ دسته تخصص حذف شد.")
        return super().delete(request, *args, **kwargs)


# ----------------------------
# مدیریت تخصص‌ها
# ----------------------------
@method_decorator(login_required, name='dispatch')
class SpecialtyListView(RoleRequiredMixin, ListView):
    model = Specialty
    template_name = "doctors/specialty_list.html"
    context_object_name = "specialties"
    required_roles = ["admin", "hr"]


@method_decorator(login_required, name='dispatch')
class SpecialtyCreateView(RoleRequiredMixin, CreateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = "doctors/specialty_form.html"
    success_url = reverse_lazy("doctors:specialty-list")
    required_roles = ["admin"]

    def form_valid(self, form):
        messages.success(self.request, "✅ تخصص جدید با موفقیت ایجاد شد.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class SpecialtyUpdateView(RoleRequiredMixin, UpdateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = "doctors/specialty_form.html"
    success_url = reverse_lazy("doctors:specialty-list")
    required_roles = ["admin"]

    def form_valid(self, form):
        messages.success(self.request, "✅ تخصص بروزرسانی شد.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class SpecialtyDeleteView(RoleRequiredMixin, DeleteView):
    model = Specialty
    template_name = "doctors/specialty_confirm_delete.html"
    success_url = reverse_lazy("doctors:specialty-list")
    required_roles = ["admin"]

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "❌ تخصص حذف شد.")
        return super().delete(request, *args, **kwargs)


# ----------------------------
# مدیریت پزشک‌ها
# ----------------------------
@method_decorator(login_required, name='dispatch')
class DoctorListView(RoleRequiredMixin, ListView):
    model = Doctor
    template_name = "doctors/doctor_list.html"
    context_object_name = "doctors"
    required_roles = ["admin", "hr"]


@method_decorator(login_required, name='dispatch')
class DoctorCreateView(RoleRequiredMixin, CreateView):
    model = Doctor
    form_class = DoctorForm
    template_name = "doctors/doctor_form.html"
    success_url = reverse_lazy("doctors:doctor-list")
    required_roles = ["admin"]

    def form_valid(self, form):
        messages.success(self.request, "✅ پزشک جدید با موفقیت ایجاد شد.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class DoctorUpdateView(RoleRequiredMixin, UpdateView):
    model = Doctor
    form_class = DoctorForm
    template_name = "doctors/doctor_form.html"
    success_url = reverse_lazy("doctors:doctor-list")
    required_roles = ["admin"]

    def form_valid(self, form):
        messages.success(self.request, "✅ اطلاعات پزشک بروزرسانی شد.")
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class DoctorDeleteView(RoleRequiredMixin, DeleteView):
    model = Doctor
    template_name = "doctors/doctor_confirm_delete.html"
    success_url = reverse_lazy("doctors:doctor-list")
    required_roles = ["admin"]

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "❌ پزشک حذف شد.")
        return super().delete(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class DoctorDetailView(RoleRequiredMixin, DetailView):
    model = Doctor
    template_name = "doctors/doctor_detail.html"
    context_object_name = "doctor"
    required_roles = ["admin", "hr"]
