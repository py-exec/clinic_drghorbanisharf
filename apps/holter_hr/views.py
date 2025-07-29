# apps/holter_hr/views.py

from apps.reception.models import ReceptionService
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import HolterHRInstallationForm, HolterHRReceptionForm, HolterHRReadingForm
from .models import HolterHRInstallation, HolterHRReception, HolterHRReading


# --- داشبورد کاری و آرشیو ---

@login_required
@permission_required("holter_hr.view_holterhrinstallation", raise_exception=True)
def holter_hr_worklist_view(request):
    """
    داشبورد کاری تکنسین هلتر ضربان.
    """
    today = timezone.now().date()

    # ۱. ID سرویس‌هایی که قبلا برایشان نصب ثبت شده
    installed_service_ids = HolterHRInstallation.objects.values_list('object_id', flat=True)

    # ۲. لیست انتظار نصب
    waiting_list = ReceptionService.objects.filter(
        tariff__service_type__code='holter_hr',
        created_at__date=today,
        status__in=['pending', 'in_progress']
    ).exclude(
        id__in=installed_service_ids
    ).select_related('reception__patient__user').order_by('created_at')

    # ۳. لیست انتظار بازگشت
    pending_return = HolterHRInstallation.objects.filter(
        reception_record__isnull=True
    ).select_related('patient').order_by('install_datetime')

    # ۴. لیست انتظار خوانش
    pending_reading = HolterHRInstallation.objects.filter(
        reception_record__isnull=False,
        reading__isnull=True
    ).select_related('patient', 'reception_record').order_by('reception_record__receive_datetime')

    context = {
        'waiting_list': waiting_list,
        'pending_return_list': pending_return,
        'pending_reading_list': pending_reading,
    }
    return render(request, 'holter_hr/holter_hr_worklist.html', context)


@login_required
@permission_required("holter_hr.view_holterhrinstallation", raise_exception=True)
def holter_hr_archive_view(request):
    """
    آرشیو تمام گزارش‌های هلتر ضربان.
    """
    archive_list = HolterHRInstallation.objects.select_related(
        'patient__user', 'technician'
    ).prefetch_related(
        'reception_record', 'reading'
    ).order_by('-install_datetime')

    paginator = Paginator(archive_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'holter_hr/holter_hr_archive.html', context)


# --- مدیریت گزارش ---

class HolterHRDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = HolterHRInstallation
    template_name = 'holter_hr/holter_hr_detail.html'
    context_object_name = 'installation'
    permission_required = "holter_hr.view_holterhrinstallation"


class HolterHRDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = HolterHRInstallation
    template_name = 'holter_hr/holter_hr_confirm_delete.html'
    permission_required = 'holter_hr.delete_holterhrinstallation'

    def get_success_url(self):
        messages.warning(self.request, "فرآیند هلتر ضربان با موفقیت حذف شد.")
        return reverse('holter_hr:holter_hr_worklist')


# --- مرحله ۱: نصب ---

class HolterHRInstallationCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = HolterHRInstallation
    form_class = HolterHRInstallationForm
    template_name = 'holter_hr/holter_hr_install_form.html'
    permission_required = 'holter_hr.add_holterhrinstallation'

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


class HolterHRInstallationUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterHRInstallation
    form_class = HolterHRInstallationForm
    template_name = 'holter_hr/holter_hr_install_form.html'
    permission_required = 'holter_hr.change_holterhrinstallation'

    def get_success_url(self):
        messages.success(self.request, "اطلاعات نصب با موفقیت ویرایش شد.")
        return self.object.get_absolute_url()


# --- مرحله ۲: دریافت ---

class HolterHRReceptionCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = HolterHRReception
    form_class = HolterHRReceptionForm
    template_name = 'holter_hr/holter_hr_reception_form.html'
    permission_required = 'holter_hr.add_holterhrreception'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['installation'] = get_object_or_404(HolterHRInstallation, pk=self.kwargs['installation_pk'])
        return context

    def form_valid(self, form):
        installation = get_object_or_404(HolterHRInstallation, pk=self.kwargs['installation_pk'])
        if hasattr(installation, 'reception_record'):
            messages.warning(self.request, "برای این نصب، قبلاً اطلاعات دریافت ثبت شده است.")
            return redirect(installation.get_absolute_url())

        form.instance.installation = installation
        messages.success(self.request, "مرحله دریافت دستگاه با موفقیت ثبت شد.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterHRReceptionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterHRReception
    form_class = HolterHRReceptionForm
    template_name = 'holter_hr/holter_hr_reception_form.html'
    permission_required = 'holter_hr.change_holterhrreception'

    def get_success_url(self):
        messages.success(self.request, "اطلاعات دریافت با موفقیت ویرایش شد.")
        return self.object.installation.get_absolute_url()


# --- مرحله ۳: خوانش ---

class HolterHRReadingCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = HolterHRReading
    form_class = HolterHRReadingForm
    template_name = 'holter_hr/holter_hr_reading_form.html'
    permission_required = 'holter_hr.add_holterhrreading'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['installation'] = get_object_or_404(HolterHRInstallation, pk=self.kwargs['installation_pk'])
        return context

    def form_valid(self, form):
        installation = get_object_or_404(HolterHRInstallation, pk=self.kwargs['installation_pk'])
        if hasattr(installation, 'reading'):
            messages.warning(self.request, "برای این نصب، قبلاً گزارش خوانش ثبت شده است.")
            return redirect(installation.get_absolute_url())

        form.instance.installation = installation
        messages.success(self.request, "گزارش خوانش با موفقیت ثبت شد.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterHRReadingUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterHRReading
    form_class = HolterHRReadingForm
    template_name = 'holter_hr/holter_hr_reading_form.html'
    permission_required = 'holter_hr.change_holterhrreading'

    def get_success_url(self):
        messages.success(self.request, "گزارش خوانش با موفقیت ویرایش شد.")
        return self.object.installation.get_absolute_url()
