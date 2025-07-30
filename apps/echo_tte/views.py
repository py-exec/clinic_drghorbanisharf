# apps/echo_tte/views.py

from django.contrib.contenttypes.models import ContentType
from apps.reception.models import ReceptionService, ServiceType, ReceptionServiceStatus
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
# Correct import for timezone:
from django.utils import timezone # <--- Ensure this is the correct import
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models.expressions import Exists
from django.db.models import Subquery, OuterRef, F, Count

# Import your models and form
from .models import TTEEchoReport
from .forms import TTEEchoReportForm


# --- Worklist and List Views ---

@login_required
@permission_required("echo_tte.view_tteechoreport", raise_exception=True)
def echo_tte_worklist_view(request):
    """
    داشبورد کاری اکوکاردیوگرافی (TTE).
    نمایش بیماران در صف انتظار برای انجام اکو.
    """
    today = timezone.now().date()

    # Subquery برای گرفتن آخرین وضعیت هر ReceptionService
    latest_service_status_subquery = Subquery(
        ReceptionServiceStatus.objects.filter(
            reception_service=OuterRef('pk')
        ).order_by('-timestamp').values('status')[:1]
    )

    # Get the ServiceType object for TTE Echo (using the code 'TTE')
    tte_service_type = None
    try:
        tte_service_type = ServiceType.objects.get(code='TTE_ECHO')  # Assuming 'TTE' is the code for TTE Echo
    except ServiceType.DoesNotExist:
        messages.error(request, "نوع خدمت 'اکوکاردیوگرافی (TTE)' (کد TTE) در سیستم یافت نشد. لطفاً آن را ایجاد کنید.")
        context = {
            'waiting_for_echo_list': [],
            'done_today': 0,
            'in_queue_total': 0,
        }
        return render(request, 'echo_tte/echo_tte_worklist.html', context)

    # Base query for all TTE Echo services for today, with latest ReceptionService status
    # TTE is a single-stage service, so we mostly care about its ReceptionService status
    tte_relevant_reception_services = ReceptionService.objects.filter(
        tariff__service_type=tte_service_type,  # Filter by the correct service type ('TTE')
        created_at__date=today,  # Services created today
    ).annotate(
        latest_service_status=latest_service_status_subquery
    ).select_related(
        'reception__patient__user', 'tariff__service_type'
    )

    # Check existence of TTEEchoReport for each ReceptionService
    reception_service_content_type = ContentType.objects.get_for_model(ReceptionService)
    has_tte_report_qs = Exists(
        TTEEchoReport.objects.filter(
            content_type=reception_service_content_type,
            object_id=OuterRef('pk')
        )
    )

    # Annotate relevant ReceptionServices with the existence flag
    tte_reception_services_annotated = tte_relevant_reception_services.annotate(
        _has_report=has_tte_report_qs,
    )

    # 1. لیست انتظار اکو (ReceptionServices that need an TTE Echo Report)
    waiting_for_echo_list = tte_reception_services_annotated.filter(
        latest_service_status__in=['pending', 'started', 'in_progress'],
        # Or whatever statuses mean 'not completed yet'
        _has_report=False  # Only services without a final TTE Report yet
    ).order_by('created_at')

    # Calculate Dashboard Stats
    done_today = tte_reception_services_annotated.filter(latest_service_status='completed').count()
    in_queue_total = waiting_for_echo_list.count()  # For single-stage, this is often just the main queue count

    context = {
        'waiting_for_echo_list': waiting_for_echo_list,
        'done_today': done_today,
        'in_queue_total': in_queue_total,
    }
    return render(request, 'echo_tte/echo_tte_worklist.html', context)


class TTEEchoReportListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = TTEEchoReport
    template_name = 'echo_tte/echo_tte_list.html'
    context_object_name = 'reports'
    paginate_by = 15  # Add pagination
    permission_required = "echo_tte.view_tteechoreport"

    def get_queryset(self):
        # Prefetch related data for efficiency
        return TTEEchoReport.objects.select_related("patient", "prescription", "technician",
                                                    "reporting_physician").order_by("-exam_datetime")


class TTEEchoReportDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = TTEEchoReport
    template_name = 'echo_tte/echo_tte_detail.html'
    context_object_name = 'report'
    permission_required = "echo_tte.view_tteechoreport"


class TTEEchoReportCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = TTEEchoReport
    form_class = TTEEchoReportForm
    template_name = 'echo_tte/tte_echo_form.html'
    permission_required = 'echo_tte.add_tteechoreport'

    def get_initial(self):
        initial = super().get_initial()
        # Set technician and exam_datetime to current user and current time
        initial['technician'] = self.request.user
        initial['exam_datetime'] = timezone.now()
        # You might also want to set reporting_physician if it's typically the current user
        # initial['reporting_physician'] = self.request.user 
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch patient and related ReceptionService
        service_id = self.kwargs.get('service_id')
        if service_id:
            service = get_object_or_404(ReceptionService, pk=service_id)
            context['service'] = service
            context['patient'] = service.reception.patient
            # Filter prescriptions for the current patient
            context['prescriptions'] = Prescription.objects.filter(patient=service.reception.patient).order_by(
                "-created_at")
            # If the form uses 'prescription' field and you want to pre-select, do it in initial
            # For simplicity, form's prescription field will show all, user picks.
        else:
            # Handle case where report is created directly for a patient (not via service ID)
            # You might have a separate URL for this, or make patient_id a kwarg
            patient_id = self.kwargs.get('patient_id')  # If URL is /create/for-patient/<int:patient_id>/
            if patient_id:
                patient = get_object_or_404(Patient, id=patient_id)
                context['patient'] = patient
                context['prescriptions'] = Prescription.objects.filter(patient=patient).order_by("-created_at")
            else:
                messages.warning(self.request, "برای ثبت گزارش اکو، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
        return context

    def form_valid(self, form):
        service_id = self.kwargs.get('service_id')
        if service_id:
            reception_service = get_object_or_404(ReceptionService, pk=service_id)
            # Check if a report already exists for this service
            if TTEEchoReport.objects.filter(reception_service=reception_service).exists():
                messages.warning(self.request,
                                 "برای این خدمت، قبلاً گزارش اکو ثبت شده است. به صفحه ویرایش هدایت می‌شوید.")
                existing_report = TTEEchoReport.objects.get(reception_service=reception_service)
                return redirect(reverse('tte:tte_update', kwargs={'pk': existing_report.pk}))

            form.instance.reception_service = reception_service
            form.instance.patient = reception_service.reception.patient  # Patient from ReceptionService
        else:
            # Handle creation for a patient without a specific ReceptionService
            patient_id = self.kwargs.get('patient_id')
            if patient_id:
                form.instance.patient = get_object_or_404(Patient, id=patient_id)
            else:
                messages.error(self.request, "برای ثبت گزارش اکو، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                return redirect(reverse('some_error_or_redirect_url'))  # Redirect to a safe page

        form.instance.created_by = self.request.user  # Set the user who created the report

        response = super().form_valid(form)  # Save the report instance

        # The TTEEchoReport.save() method now handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✅ گزارش اکوکاردیوگرافی (TTE) با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        # Redirect to the worklist or the detail page of the created report
        return reverse('tte:tte_detail', kwargs={'pk': self.object.pk})


class TTEEchoReportUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = TTEEchoReport
    form_class = TTEEchoReportForm
    template_name = 'echo_tte/tte_echo_form.html'  # Reusing the form template
    context_object_name = 'report'
    permission_required = 'echo_tte.change_tteechoreport'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure patient and prescriptions are available for the form if needed
        context['patient'] = self.object.patient
        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient).order_by("-created_at")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)  # Save the updated report instance

        # The TTEEchoReport.save() method handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✏️ گزارش اکوکاردیوگرافی (TTE) با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
        return reverse('tte:tte_detail', kwargs={'pk': self.object.pk})


class TTEEchoReportDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = TTEEchoReport
    template_name = 'echo_tte/tte_confirm_delete.html'
    context_object_name = 'report'
    permission_required = 'echo_tte.delete_tteechoreport'

    def get_success_url(self):
        # If a TTE report is deleted, you might want to revert the ReceptionService status
        # For simplicity now, we just redirect.
        messages.warning(self.request, "🗑️ گزارش اکوکاردیوگرافی (TTE) با موفقیت حذف شد.")
        return reverse_lazy('tte:tte_list')  # Redirect to the list view


# Helper function to convert CharField ('بله'/'خیر') to Boolean for old POST data
def convert_to_boolean(value):
    if value == "بله":
        return True
    elif value == "خیر":
        return False
    return None  # Or False if default is False