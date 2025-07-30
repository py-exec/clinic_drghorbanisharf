# apps/holter_bp/views.py

from django.contrib.contenttypes.models import ContentType
from apps.reception.models import ReceptionService, ServiceType, ReceptionServiceStatus
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models.expressions import Exists
from django.db.models import Subquery, OuterRef, F, Count

from .forms import HolterBPInstallationForm, HolterBPReceptionForm, HolterBPReadingForm
from .models import HolterBPInstallation, HolterBPReception, HolterBPReading, \
    HolterBPInstallationStatus, HolterBPReceptionStatus, HolterBPReadingStatus


# --- داشبورد کاری و آرشیو ---


@login_required
@permission_required("holter_bp.view_holterbpinstallation", raise_exception=True)
def holter_bp_worklist_view(request):
    """
    داشبورد کاری کامل تکنسین هلتر فشار با آمار و صف‌های کاری.
    """
    today = timezone.now().date()

    # Subquery برای گرفتن آخرین وضعیت هر ReceptionService
    latest_service_status_subquery = Subquery(
        ReceptionServiceStatus.objects.filter(
            reception_service=OuterRef('pk')
        ).order_by('-timestamp').values('status')[:1]
    )

    # Get the ServiceType object for Holter BP (using the code 'BP')
    holter_bp_service_type = None
    try:
        holter_bp_service_type = ServiceType.objects.get(code='BP')
    except ServiceType.DoesNotExist:
        messages.error(request, "نوع خدمت 'هولتر فشار' (کد BP) در سیستم یافت نشد. لطفاً آن را ایجاد کنید.")
        # If service type is not found, return empty lists and 0 for stats
        context = {
            'waiting_for_install_list': [],
            'waiting_for_return_list': [],
            'waiting_for_reading_list': [],
            'done_today': 0,
            'in_queue_total': 0,
        }
        return render(request, 'holter_bp/holter_bp_worklist.html', context)

    # Base query for all Holter BP services for today, with latest ReceptionService status
    holter_relevant_reception_services = ReceptionService.objects.filter(
        tariff__service_type=holter_bp_service_type,  # Filter by the correct service type ('BP')
        created_at__date=today,  # Services created today
    ).annotate(
        latest_service_status=latest_service_status_subquery  # This is the status from ReceptionServiceStatus
    ).select_related(
        'reception__patient__user', 'tariff__service_type'
    )

    # Dynamic Exists checks (always based on ReceptionService PK and GFK fields)
    reception_service_content_type = ContentType.objects.get_for_model(ReceptionService)

    has_holter_installation_qs = Exists(
        HolterBPInstallation.objects.filter(
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

    # 2. لیست انتظار بازگشت (HolterBPInstallations that have been installed but not received)
    # This query directly starts from HolterBPInstallation, which has direct FKs to patient
    waiting_for_return_list = HolterBPInstallation.objects.filter(
        content_type=reception_service_content_type,  # GFK content_type
        object_id__in=holter_relevant_reception_services.values('pk'),  # Link to relevant ReceptionServices
        reception_record__isnull=True  # No reception record yet
    ).select_related('patient').order_by('install_datetime')

    # 3. لیست انتظار خوانش (HolterBPInstallations that have been received but not read)
    # This query directly starts from HolterBPInstallation
    waiting_for_reading_list = HolterBPInstallation.objects.filter(
        content_type=reception_service_content_type,  # GFK content_type
        object_id__in=holter_relevant_reception_services.values('pk'),  # Link to relevant ReceptionServices
        reception_record__isnull=False,  # Has a reception record
        reading__isnull=True  # No reading record yet
    ).select_related('patient', 'reception_record').order_by('reception_record__receive_datetime')

    # Calculate Dashboard Stats
    # Re-annotate the original set of today's holter services with all existence flags for accurate counting.
    has_holter_reception_qs_for_stats = Exists(
        HolterBPReception.objects.filter(
            installation__content_type=reception_service_content_type,
            installation__object_id=OuterRef('pk')
        )
    )
    has_holter_reading_qs_for_stats = Exists(
        HolterBPReading.objects.filter(
            installation__content_type=reception_service_content_type,
            installation__object_id=OuterRef('pk')
        )
    )

    holter_services_for_stats = holter_relevant_reception_services.annotate(
        _has_installation=has_holter_installation_qs,  # Already defined above
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
        if HolterBPInstallation.objects.filter(reception_service=reception_service).exists():
            messages.warning(self.request, "برای این خدمت قبلاً رکورد نصب هلتر ثبت شده است.")
            # اگر وجود دارد، به صفحه جزئیات آن ریدایرکت کن
            existing_installation = HolterBPInstallation.objects.get(reception_service=reception_service)
            return redirect(existing_installation.get_absolute_url())

        form.instance.reception_service = reception_service
        form.instance.patient = reception_service.reception.patient
        form.instance.created_by = self.request.user  # This is redundant if technician is created_by, but safe to keep

        response = super().form_valid(form)  # Save the installation first

        # IMPORTANT: No direct change_service_status call here.
        # It's handled by HolterBPInstallation.save() (which creates HolterBPInstallationStatus)
        # and HolterBPInstallationStatus.save() (which updates HolterBPInstallation.latest_installation_status)
        # and then by signals.py (which updates ReceptionServiceStatus).

        messages.success(self.request, "مرحله نصب دستگاه با موفقیت ثبت شد.")
        return response


class HolterBPInstallationUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterBPInstallation
    form_class = HolterBPInstallationForm
    template_name = 'holter_bp/holter_bp_install_form.html'
    permission_required = 'holter_bp.change_holterbpinstallation'

    def form_valid(self, form):
        response = super().form_valid(form)
        # No direct change_service_status call here
        messages.success(self.request, "اطلاعات نصب با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
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

        response = super().form_valid(form)

        # IMPORTANT: No direct change_service_status call here.
        # It's handled by HolterBPReception.save() (which creates HolterBPReceptionStatus)
        # and HolterBPReceptionStatus.save() (which updates HolterBPReception.latest_reception_status)
        # and then by signals.py.

        messages.success(self.request, "مرحله دریافت دستگاه با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterBPReceptionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterBPReception
    form_class = HolterBPReceptionForm
    template_name = 'holter_bp/holter_bp_reception_form.html'
    permission_required = 'holter_bp.change_holterbpreception'

    def form_valid(self, form):
        response = super().form_valid(form)
        # No direct change_service_status call here
        messages.success(self.request, "اطلاعات دریافت با موفقیت ویرایش شد.")
        return response

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

        response = super().form_valid(form)

        # IMPORTANT: No direct change_service_status call here.
        # It's handled by HolterBPReading.save() (which creates HolterBPReadingStatus)
        # and HolterBPReadingStatus.save() (which updates HolterBPReading.latest_reading_status)
        # and then by signals.py.

        messages.success(self.request, "گزارش خوانش با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        return self.object.installation.get_absolute_url()


class HolterBPReadingUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = HolterBPReading
    form_class = HolterBPReadingForm
    template_name = 'holter_bp/holter_bp_reading_form.html'
    permission_required = 'holter_bp.change_holterbpreading'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات خوانش با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
        messages.success(self.request, "اطلاعات خوانش با موفقیت ویرایش شد.")
        return self.object.installation.get_absolute_url()