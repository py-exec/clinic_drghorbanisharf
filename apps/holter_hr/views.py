# apps/holter_hr/views.py

from django.contrib.contenttypes.models import ContentType
from apps.reception.models import ReceptionService, ServiceType, ReceptionServiceStatus
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone  # Make sure timezone is imported
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models.expressions import Exists
from django.db.models import Subquery, OuterRef, F, Count

from .forms import HolterHRInstallationForm, HolterHRReceptionForm, HolterHRReadingForm
from .models import HolterHRInstallation, HolterHRReception, HolterHRReading, \
    HolterHRInstallationStatus, HolterHRReceptionStatus, HolterHRReadingStatus


# --- داشبورد کاری و آرشیو ---


@login_required
@permission_required("holter_hr.view_holterhrinstallation", raise_exception=True)
def holter_hr_worklist_view(request):
    """
    داشبورد کاری تکنسین هلتر ضربان.
    """
    today = timezone.now().date()

    # Subquery برای گرفتن آخرین وضعیت هر ReceptionService
    latest_service_status_subquery = Subquery(
        ReceptionServiceStatus.objects.filter(
            reception_service=OuterRef('pk')
        ).order_by('-timestamp').values('status')[:1]
    )

    # Get the ServiceType object for Holter HR (using the correct code 'HR')
    holter_hr_service_type = None
    try:
        holter_hr_service_type = ServiceType.objects.get(code='HR')
    except ServiceType.DoesNotExist:
        messages.error(request, "نوع خدمت 'هولتر ریتم' (کد HR) در سیستم یافت نشد. لطفاً آن را ایجاد کنید.")
        # If service type is not found, return empty lists and 0 for stats
        context = {
            'waiting_for_install_list': [],
            'waiting_for_return_list': [],
            'waiting_for_reading_list': [],
            'done_today': 0,
            'in_queue_total': 0,
        }
        return render(request, 'holter_hr/holter_hr_worklist.html', context)

    # Base query for all Holter HR services for today, with latest ReceptionService status
    # This query focuses on ReceptionService objects
    holter_relevant_reception_services = ReceptionService.objects.filter(
        tariff__service_type=holter_hr_service_type,
        created_at__date=today,
    ).annotate(
        latest_service_status=latest_service_status_subquery
    ).select_related(
        'reception__patient__user', 'tariff__service_type'  # These select_relateds are on ReceptionService
    )

    # Dynamic Exists checks (always based on ReceptionService PK and GFK fields)
    reception_service_content_type = ContentType.objects.get_for_model(ReceptionService)

    has_holter_installation_qs = Exists(
        HolterHRInstallation.objects.filter(
            content_type=reception_service_content_type,
            object_id=OuterRef('pk')
        )
    )

    # Annotate holter_relevant_reception_services for the 'install' queue and for stats calculation
    holter_reception_services_annotated_for_install = holter_relevant_reception_services.annotate(
        _has_installation=has_holter_installation_qs,
    )

    # 1. لیست انتظار نصب (ReceptionServices that need an installation)
    waiting_for_install_list = holter_reception_services_annotated_for_install.filter(
        latest_service_status__in=['pending', 'started'],
        _has_installation=False  # Only services without an installation yet
    ).order_by('created_at')

    # 2. لیست انتظار بازگشت (HolterHRInstallations that have been installed but not received)
    # This query directly starts from HolterHRInstallation, which has direct FKs to patient
    waiting_for_return_list = HolterHRInstallation.objects.filter(
        # Filter these installations to ensure they link to relevant ReceptionServices
        content_type=reception_service_content_type,
        object_id__in=holter_relevant_reception_services.values('pk'),
        reception_record__isnull=True  # No reception record yet
    ).select_related('patient').order_by('install_datetime')

    # 3. لیست انتظار خوانش (HolterHRInstallations that have been received but not read)
    # This query directly starts from HolterHRInstallation
    waiting_for_reading_list = HolterHRInstallation.objects.filter(
        # Filter these installations to ensure they link to relevant ReceptionServices
        content_type=reception_service_content_type,
        object_id__in=holter_relevant_reception_services.values('pk'),
        reception_record__isnull=False,  # Has a reception record
        reading__isnull=True  # No reading record yet
    ).select_related('patient', 'reception_record').order_by('reception_record__receive_datetime')

    # Calculate Dashboard Stats
    # Re-annotate the original set of today's holter services with all existence flags for accurate counting.
    has_holter_reception_qs_for_stats = Exists(
        HolterHRReception.objects.filter(
            installation__content_type=reception_service_content_type,
            installation__object_id=OuterRef('pk')
        )
    )
    has_holter_reading_qs_for_stats = Exists(
        HolterHRReading.objects.filter(
            installation__content_type=reception_service_content_type,
            installation__object_id=OuterRef('pk')
        )
    )

    holter_services_for_stats = holter_relevant_reception_services.annotate(
        _has_installation=has_holter_installation_qs,
        _has_reception=has_holter_reception_qs_for_stats,
        _has_reading=has_holter_reading_qs_for_stats
    )

    done_today = holter_services_for_stats.filter(latest_service_status='completed').count()

    # Ensure in_queue_total sums the counts from the *actual lists* used for display
    in_queue_total = waiting_for_install_list.count() + waiting_for_return_list.count() + waiting_for_reading_list.count()

    context = {
        'waiting_for_install_list': waiting_for_install_list,
        'waiting_for_return_list': waiting_for_return_list,
        'waiting_for_reading_list': waiting_for_reading_list,
        'done_today': done_today,
        'in_queue_total': in_queue_total,
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
        # NEW: Set technician and install_datetime to current user and current time
        return {
            'technician': self.request.user,
            'install_datetime': timezone.now()  # Current time
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = get_object_or_404(ReceptionService, pk=self.kwargs['service_id'])
        return context

    def form_valid(self, form):
        reception_service = get_object_or_404(ReceptionService, pk=self.kwargs['service_id'])

        # بررسی اگر قبلا نصب ثبت شده باشد
        if HolterHRInstallation.objects.filter(reception_service=reception_service).exists():
            messages.warning(self.request, "برای این خدمت قبلاً رکورد نصب هلتر ثبت شده است.")
            # اگر وجود دارد، به صفحه جزئیات آن ریدایرکت کن
            existing_installation = HolterHRInstallation.objects.get(reception_service=reception_service)
            return redirect(existing_installation.get_absolute_url())

        form.instance.reception_service = reception_service
        form.instance.patient = reception_service.reception.patient
        form.instance.created_by = self.request.user  # This is redundant if technician is created_by, but safe to keep

        response = super().form_valid(form)

        messages.success(self.request, "مرحله نصب دستگاه با موفقیت ثبت شد.")
        return response


class HolterHRInstallationUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterHRInstallation
    form_class = HolterHRInstallationForm
    template_name = 'holter_hr/holter_hr_install_form.html'
    permission_required = 'holter_hr.change_holterhrinstallation'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات نصب با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
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

        response = super().form_valid(form)

        messages.success(self.request, "مرحله دریافت دستگاه با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterHRReceptionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterHRReception
    form_class = HolterHRReceptionForm
    template_name = 'holter_hr/holter_hr_reception_form.html'
    permission_required = 'holter_hr.change_holterhrreception'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات دریافت با موفقیت ویرایش شد.")
        return response

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

        response = super().form_valid(form)

        messages.success(self.request, "گزارش خوانش با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterHRReadingUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterHRReading
    form_class = HolterHRReadingForm
    template_name = 'holter_hr/holter_hr_reading_form.html'
    permission_required = 'holter_hr.change_holterhrreading'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات خوانش با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
        messages.success(self.request, "اطلاعات خوانش با موفقیت ویرایش شد.")
        return self.object.installation.get_absolute_url()