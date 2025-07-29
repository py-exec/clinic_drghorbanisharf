# apps/holter_bp/views.py

from apps.appointments.models import Appointment
from apps.reception.models import ReceptionService
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import HolterBPInstallationForm, HolterBPReceptionForm, HolterBPReadingForm
from .models import HolterBPInstallation, HolterBPReception, HolterBPReading


# --- داشبورد کاری و آرشیو ---

@login_required
@permission_required("holter_bp.view_holterbpinstallation", raise_exception=True)
def holter_bp_worklist_view(request):
    """
    داشبورد کاری کامل تکنسین هلتر فشار با آمار و صف‌های کاری.
    """
    today = timezone.now().date()

    # --- محاسبه آمار بالای صفحه ---

    # تعداد نصب‌هایی که امروز تکمیل شده و گزارش خوانش برای آنها ثبت شده
    done_today_count = HolterBPReading.objects.filter(
        read_datetime__date=today
    ).count()

    # --- تهیه لیست‌های کاری ---

    # ۱. لیست انتظار نصب
    installed_service_ids = HolterBPInstallation.objects.values_list('object_id', flat=True)
    waiting_for_install_list = ReceptionService.objects.filter(
        tariff__service_type__code='holter_bp',
        created_at__date=today,
        status__in=['pending', 'in_progress']
    ).exclude(
        id__in=installed_service_ids
    ).select_related('reception__patient__user').order_by('created_at')

    # ۲. لیست انتظار بازگشت
    waiting_for_return_list = HolterBPInstallation.objects.filter(
        reception_record__isnull=True
    ).select_related('patient').order_by('install_datetime')

    # ۳. لیست انتظار خوانش
    waiting_for_reading_list = HolterBPInstallation.objects.filter(
        reception_record__isnull=False,
        reading__isnull=True
    ).select_related('patient', 'reception_record').order_by('reception_record__receive_datetime')

    # تعداد کل وظایف امروز (نصب + بازگشت + خوانش)
    total_tasks_count = waiting_for_install_list.count() + waiting_for_return_list.count() + waiting_for_reading_list.count()

    context = {
        'done_today': done_today_count,
        'in_queue_total': total_tasks_count,  # مجموع تمام صف‌ها
        'waiting_for_install_list': waiting_for_install_list,
        'waiting_for_return_list': waiting_for_return_list,
        'waiting_for_reading_list': waiting_for_reading_list,
    }
    return render(request, 'holter_bp/holter_bp_worklist.html', context)


@login_required
@permission_required("holter_bp.view_holterbpinstallation", raise_exception=True)
def holter_bp_archive_view(request):
    """
    آرشیو تمام گزارش‌های هلتر فشار با کوئری بهینه شده.
    """
    archive_list = HolterBPInstallation.objects.select_related(
        'patient__user', 'technician'
    ).prefetch_related(
        'reception_record', 'reading'
    ).order_by('-install_datetime')

    paginator = Paginator(archive_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'holter_bp/holter_bp_archive.html', context)


# --- مدیریت گزارش ---

class HolterBPDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = HolterBPInstallation
    template_name = 'holter_bp/holter_bp_detail.html'
    context_object_name = 'installation'
    permission_required = "holter_bp.view_holterbpinstallation"


class HolterBPDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = HolterBPInstallation
    template_name = 'holter_bp/holter_bp_confirm_delete.html'
    permission_required = 'holter_bp.delete_holterbpinstallation'

    def get_success_url(self):
        messages.warning(self.request, "فرآیند هلتر با موفقیت حذف شد.")
        return reverse('holter_bp:holter_bp_worklist')


# --- مرحله ۱: نصب ---

class HolterBPInstallationCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = HolterBPInstallation
    form_class = HolterBPInstallationForm
    template_name = 'holter_bp/holter_bp_install_form.html'
    permission_required = 'holter_bp.add_holterbpinstallation'

    def get_initial(self):
        return {'technician': self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = get_object_or_404(ReceptionService, pk=self.kwargs['service_id'])
        return context

    def form_valid(self, form):
        reception_service = get_object_or_404(ReceptionService, pk=self.kwargs['service_id'])
        form.instance.reception_service = reception_service
        form.instance.patient = reception_service.reception.patient
        form.instance.created_by = self.request.user
        messages.success(self.request, "مرحله نصب دستگاه با موفقیت ثبت شد.")
        return super().form_valid(form)


class HolterBPInstallationUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterBPInstallation
    form_class = HolterBPInstallationForm
    template_name = 'holter_bp/holter_bp_install_form.html'
    permission_required = 'holter_bp.change_holterbpinstallation'

    def get_success_url(self):
        messages.success(self.request, "اطلاعات نصب با موفقیت ویرایش شد.")
        return self.object.get_absolute_url()


# --- مرحله ۲: دریافت ---

class HolterBPReceptionCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = HolterBPReception
    form_class = HolterBPReceptionForm
    template_name = 'holter_bp/holter_bp_reception_form.html'
    permission_required = 'holter_bp.add_holterbpreception'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['installation'] = get_object_or_404(HolterBPInstallation, pk=self.kwargs['installation_pk'])
        return context

    def form_valid(self, form):
        installation = get_object_or_404(HolterBPInstallation, pk=self.kwargs['installation_pk'])
        if hasattr(installation, 'reception_record'):
            messages.warning(self.request, "برای این نصب، قبلاً اطلاعات دریافت ثبت شده است.")
            return redirect(installation.get_absolute_url())

        form.instance.installation = installation
        messages.success(self.request, "مرحله دریافت دستگاه با موفقیت ثبت شد.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterBPReceptionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterBPReception
    form_class = HolterBPReceptionForm
    template_name = 'holter_bp/holter_bp_reception_form.html'
    permission_required = 'holter_bp.change_holterbpreception'

    def get_success_url(self):
        messages.success(self.request, "اطلاعات دریافت با موفقیت ویرایش شد.")
        return self.object.installation.get_absolute_url()


# --- مرحله ۳: خوانش ---

class HolterBPReadingCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = HolterBPReading
    form_class = HolterBPReadingForm
    template_name = 'holter_bp/holter_bp_reading_form.html'
    permission_required = 'holter_bp.add_holterbpreading'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['installation'] = get_object_or_404(HolterBPInstallation, pk=self.kwargs['installation_pk'])
        return context

    def form_valid(self, form):
        installation = get_object_or_404(HolterBPInstallation, pk=self.kwargs['installation_pk'])
        if hasattr(installation, 'reading'):
            messages.warning(self.request, "برای این نصب، قبلاً گزارش خوانش ثبت شده است.")
            return redirect(installation.get_absolute_url())

        form.instance.installation = installation
        messages.success(self.request, "گزارش خوانش با موفقیت ثبت شد.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterBPReadingUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterBPReading
    form_class = HolterBPReadingForm
    template_name = 'holter_bp/holter_bp_reading_form.html'
    permission_required = 'holter_bp.change_holterbpreading'

    def get_success_url(self):
        messages.success(self.request, "گزارش خوانش با موفقیت ویرایش شد.")
        return self.object.installation.get_absolute_url()
