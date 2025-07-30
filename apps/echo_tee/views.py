# apps/echo_tee/views.py

from django.contrib.contenttypes.models import ContentType
from apps.reception.models import ReceptionService, ServiceType, ReceptionServiceStatus
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models.expressions import Exists
from django.db.models import Subquery, OuterRef, F, Count
from django.utils import timezone  # Make sure timezone is imported

# Import your models and form
from .models import TEEEchoReport
from .forms import TEEEchoReportForm
from apps.patient.models import Patient  # Needed for patient_id based creation if applicable
from apps.prescriptions.models import Prescription  # Needed for filtering prescriptions in context


# --- Worklist and List Views ---

@login_required
@permission_required("echo_tee.view_teeechoreport", raise_exception=True)
def echo_tee_worklist_view(request):
    """
    داشبورد کاری اکو از راه مری (TEE).
    نمایش بیماران در صف انتظار برای انجام TEE.
    """
    today = timezone.now().date()

    # Subquery برای گرفتن آخرین وضعیت هر ReceptionService
    latest_service_status_subquery = Subquery(
        ReceptionServiceStatus.objects.filter(
            reception_service=OuterRef('pk')
        ).order_by('-timestamp').values('status')[:1]
    )

    # Get the ServiceType object for TEE Echo (using the code 'TEE')
    tee_service_type = None
    try:
        tee_service_type = ServiceType.objects.get(code='TEE_ECHO')  # Assuming 'TEE' is the code for TEE Echo
    except ServiceType.DoesNotExist:
        messages.error(request, "نوع خدمت 'اکو از راه مری (TEE)' (کد TEE) در سیستم یافت نشد. لطفاً آن را ایجاد کنید.")
        context = {
            'waiting_for_tee_list': [],
            'done_today': 0,
            'in_queue_total': 0,
        }
        return render(request, 'echo_tee/echo_tee_worklist.html', context)

    # Base query for all TEE Echo services for today, with latest ReceptionService status
    # TEE is a single-stage service, so we mostly care about its ReceptionService status
    tee_relevant_reception_services = ReceptionService.objects.filter(
        tariff__service_type=tee_service_type,  # Filter by the correct service type ('TEE')
        created_at__date=today,  # Services created today
    ).annotate(
        latest_service_status=latest_service_status_subquery
    ).select_related(
        'reception__patient__user', 'tariff__service_type'
    )

    # Check existence of TEEEchoReport for each ReceptionService
    reception_service_content_type = ContentType.objects.get_for_model(ReceptionService)
    has_tee_report_qs = Exists(
        TEEEchoReport.objects.filter(
            content_type=reception_service_content_type,  # Correct GFK fields
            object_id=OuterRef('pk')  # Correct GFK fields
        )
    )

    # Annotate relevant ReceptionServices with the existence flag
    tee_reception_services_annotated = tee_relevant_reception_services.annotate(
        _has_report=has_tee_report_qs,
    )

    # 1. لیست انتظار TEE (ReceptionServices that need a TEE Echo Report)
    waiting_for_tee_list = tee_reception_services_annotated.filter(
        latest_service_status__in=['pending', 'started', 'in_progress'],
        # Or whatever statuses mean 'not completed yet'
        _has_report=False  # Only services without a final TEE Report yet
    ).order_by('created_at')

    # Calculate Dashboard Stats
    done_today = tee_reception_services_annotated.filter(latest_service_status='completed').count()
    in_queue_total = waiting_for_tee_list.count()  # For single-stage, this is often just the main queue count

    context = {
        'waiting_for_tee_list': waiting_for_tee_list,
        'done_today': done_today,
        'in_queue_total': in_queue_total,
    }
    return render(request, 'echo_tee/echo_tee_worklist.html', context)


class TEEEchoReportListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = TEEEchoReport
    template_name = 'echo_tee/echo_tee_list.html'
    context_object_name = 'reports'
    paginate_by = 15  # Add pagination
    permission_required = "echo_tee.view_teeechoreport"

    def get_queryset(self):
        # Prefetch related data for efficiency
        # Note: technician/reporting_physician are not in your TEEEchoReport model.
        # If you added them as ForeignKey to User, update this.
        return TEEEchoReport.objects.select_related("patient", "prescription").order_by("-exam_datetime")


class TEEEchoReportDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = TEEEchoReport
    template_name = 'echo_tee/echo_tee_detail.html'
    context_object_name = 'report'
    permission_required = "echo_tee.view_teeechoreport"


class TEEEchoReportCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = TEEEchoReport
    form_class = TEEEchoReportForm
    template_name = 'echo_tee/tee_echo_form.html'
    permission_required = 'echo_tee.add_teeechoreport'

    def get_initial(self):
        initial = super().get_initial()
        # Set created_by and default exam_datetime to current user and current time
        initial['created_by'] = self.request.user
        initial['exam_datetime'] = timezone.now()
        # Note: technician/reporting_physician are not FK in your TEEEchoReport model currently.
        # If you change them to FK to User, you might want to set them here.
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
            # Pass initial patient and service to form (for hidden/disabled fields)
            self.form_class.base_fields['patient'].initial = service.reception.patient.pk  # Pass PK for ChoiceField
            self.form_class.base_fields['prescription'].queryset = Prescription.objects.filter(
                patient=service.reception.patient)  # Filter queryset
        else:
            # Handle case where report is created directly for a patient (not via service ID)
            # This is less recommended if all services MUST be linked to ReceptionService
            patient_id = self.kwargs.get('patient_id')
            if patient_id:
                patient = get_object_or_404(Patient, id=patient_id)
                context['patient'] = patient
                context['prescriptions'] = Prescription.objects.filter(patient=patient).order_by("-created_at")
                self.form_class.base_fields['patient'].initial = patient.pk
                self.form_class.base_fields['prescription'].queryset = Prescription.objects.filter(patient=patient)
            else:
                messages.warning(self.request, "برای ثبت گزارش اکو، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                return redirect(reverse_lazy('echo_tee:echo_tee_worklist'))  # Redirect to a safe page
        return context

    def form_valid(self, form):
        service_id = self.kwargs.get('service_id')
        if service_id:
            reception_service = get_object_or_404(ReceptionService, pk=service_id)
            # Check if a report already exists for this service
            if TEEEchoReport.objects.filter(reception_service=reception_service).exists():  # Uses GFK property directly
                messages.warning(self.request,
                                 "برای این خدمت، قبلاً گزارش اکو ثبت شده است. به صفحه ویرایش هدایت می‌شوید.")
                existing_report = TEEEchoReport.objects.get(
                    reception_service=reception_service)  # Uses GFK property directly
                return redirect(reverse('echo_tee:tee_update', kwargs={'pk': existing_report.pk}))

            form.instance.reception_service = reception_service  # Set GFK
            form.instance.patient = reception_service.reception.patient  # Patient from ReceptionService
        else:
            # Handle creation for a patient without a specific ReceptionService
            patient_id = self.kwargs.get('patient_id')
            if patient_id:
                form.instance.patient = get_object_or_404(Patient, id=patient_id)
            else:
                messages.error(self.request, "برای ثبت گزارش اکو، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                return redirect(reverse_lazy('echo_tee:echo_tee_worklist'))

        form.instance.created_by = self.request.user  # Set the user who created the report

        response = super().form_valid(form)  # Save the report instance

        # The TEEEchoReport.save() method now handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✅ گزارش اکو از راه مری (TEE) با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        # Redirect to the worklist or the detail page of the created report
        return reverse('echo_tee:tee_detail', kwargs={'pk': self.object.pk})


class TEEEchoReportUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = TEEEchoReport
    form_class = TEEEchoReportForm
    template_name = 'echo_tee/tee_echo_form.html'  # Reusing the form template
    context_object_name = 'report'
    permission_required = 'echo_tee.change_teeechoreport'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure patient and prescriptions are available for the form if needed
        context['patient'] = self.object.patient
        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient).order_by("-created_at")

        # Pass initial patient and service to form (for hidden/disabled fields)
        # Ensure the patient choice is correct for the update form too if it's disabled
        self.form_class.base_fields['patient'].initial = self.object.patient.pk
        self.form_class.base_fields['prescription'].queryset = Prescription.objects.filter(patient=self.object.patient)

        return context

    def form_valid(self, form):
        response = super().form_valid(form)  # Save the updated report instance

        # The TEEEchoReport.save() method handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✏️ گزارش اکو از راه مری (TEE) با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
        return reverse('echo_tee:tee_detail', kwargs={'pk': self.object.pk})


class TEEEchoReportDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = TEEEchoReport
    template_name = 'echo_tee/tee_confirm_delete.html'
    context_object_name = 'report'
    permission_required = 'echo_tee.delete_teeechoreport'

    def get_success_url(self):
        # If a TEE report is deleted, you might want to revert the ReceptionService status
        messages.warning(self.request, "🗑️ گزارش اکو از راه مری (TEE) با موفقیت حذف شد.")
        return reverse_lazy('echo_tee:tee_list')  # Redirect to the list view