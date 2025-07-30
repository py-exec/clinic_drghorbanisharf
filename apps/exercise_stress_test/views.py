# apps/exercise_stress_test/views.py

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
from django.utils import timezone

# Import your models and form
from .models import StressTestReport
from .forms import StressTestReportForm
from apps.patient.models import Patient  # Needed for patient context
from apps.prescriptions.models import Prescription  # Needed for prescription context


# --- Worklist and List Views ---

@login_required
@permission_required("exercise_stress_test.view_stresstestreport", raise_exception=True)
def stress_test_worklist_view(request):
    """
    داشبورد کاری تست ورزش / استرس اکو.
    نمایش بیماران در صف انتظار برای انجام تست.
    """
    today = timezone.now().date()

    # Subquery برای گرفتن آخرین وضعیت هر ReceptionService
    latest_service_status_subquery = Subquery(
        ReceptionServiceStatus.objects.filter(
            reception_service=OuterRef('pk')
        ).order_by('-timestamp').values('status')[:1]
    )

    # Get the ServiceType object for Stress Test (using the code 'STRESS')
    stress_test_service_type = None
    try:
        stress_test_service_type = ServiceType.objects.get(
            code='STRESS_TEST')  # Assuming 'STRESS' is the code for Stress Test
    except ServiceType.DoesNotExist:
        messages.error(request,
                       "نوع خدمت 'تست ورزش / استرس اکو' (کد STRESS) در سیستم یافت نشد. لطفاً آن را ایجاد کنید.")
        context = {
            'waiting_for_stress_test_list': [],
            'done_today': 0,
            'in_queue_total': 0,
        }
        return render(request, 'exercise_stress_test/stress_test_worklist.html', context)

    # Base query for all Stress Test services for today, with latest ReceptionService status
    stress_test_relevant_reception_services = ReceptionService.objects.filter(
        tariff__service_type=stress_test_service_type,  # Filter by the correct service type ('STRESS')
        created_at__date=today,  # Services created today
    ).annotate(
        latest_service_status=latest_service_status_subquery
    ).select_related(
        'reception__patient__user', 'tariff__service_type'
    )

    # Check existence of StressTestReport for each ReceptionService
    reception_service_content_type = ContentType.objects.get_for_model(ReceptionService)
    has_stress_test_report_qs = Exists(
        StressTestReport.objects.filter(
            content_type=reception_service_content_type,  # Correct GFK fields
            object_id=OuterRef('pk')  # Correct GFK fields
        )
    )

    # Annotate relevant ReceptionServices with the existence flag
    stress_test_reception_services_annotated = stress_test_relevant_reception_services.annotate(
        _has_report=has_stress_test_report_qs,
    )

    # 1. لیست انتظار تست ورزش (ReceptionServices that need a StressTestReport)
    waiting_for_stress_test_list = stress_test_reception_services_annotated.filter(
        latest_service_status__in=['pending', 'started', 'in_progress'],
        # Or whatever statuses mean 'not completed yet'
        _has_report=False  # Only services without a final StressTest Report yet
    ).order_by('created_at')

    # Calculate Dashboard Stats
    done_today = stress_test_reception_services_annotated.filter(latest_service_status='completed').count()
    in_queue_total = waiting_for_stress_test_list.count()  # For single-stage, this is often just the main queue count

    context = {
        'waiting_for_stress_test_list': waiting_for_stress_test_list,
        'done_today': done_today,
        'in_queue_total': in_queue_total,
    }
    return render(request, 'exercise_stress_test/stress_test_worklist.html', context)


class StressTestReportListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = StressTestReport
    template_name = 'exercise_stress_test/stress_test_list.html'
    context_object_name = 'reports'
    paginate_by = 15  # Add pagination
    permission_required = "exercise_stress_test.view_stresstestreport"

    def get_queryset(self):
        # Prefetch related data for efficiency
        return StressTestReport.objects.select_related(
            "patient", "prescription", "created_by"
        ).order_by("-created_at")


class StressTestReportDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = StressTestReport
    template_name = 'exercise_stress_test/stress_test_detail.html'
    context_object_name = 'report'
    permission_required = "exercise_stress_test.view_stresstestreport"


class StressTestReportCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = StressTestReport
    form_class = StressTestReportForm
    template_name = 'exercise_stress_test/stress_test_form.html'
    permission_required = 'exercise_stress_test.add_stresstestreport'

    def get_initial(self):
        initial = super().get_initial()
        # Set created_by and default exam_datetime to current user and current time
        initial['created_by'] = self.request.user
        initial['exam_datetime'] = timezone.now()
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
            # Make sure to set initial for patient if the form field is designed to be set programmatically
            self.form_class.base_fields['patient'].initial = service.reception.patient.pk  # Pass PK for ChoiceField
            self.form_class.base_fields['prescription'].queryset = Prescription.objects.filter(
                patient=service.reception.patient)  # Filter queryset
        else:
            # Handle case where report is created directly for a patient (not via service ID)
            patient_id = self.kwargs.get('patient_id')
            if patient_id:
                patient = get_object_or_404(Patient, id=patient_id)
                context['patient'] = patient
                context['prescriptions'] = Prescription.objects.filter(patient=patient).order_by("-created_at")
                self.form_class.base_fields['patient'].initial = patient.pk
                self.form_class.base_fields['prescription'].queryset = Prescription.objects.filter(patient=patient)
            else:
                messages.warning(self.request, "برای ثبت گزارش تست ورزش، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                # Fallback redirect, define a safe URL
                return redirect(reverse_lazy('exercise_stress_test:stress_test_worklist'))
        return context

    def form_valid(self, form):
        service_id = self.kwargs.get('service_id')
        if service_id:
            reception_service = get_object_or_404(ReceptionService, pk=service_id)
            # Check if a report already exists for this service
            if StressTestReport.objects.filter(
                    reception_service=reception_service).exists():  # Uses GFK property directly
                messages.warning(self.request,
                                 "برای این خدمت، قبلاً گزارش تست ورزش ثبت شده است. به صفحه ویرایش هدایت می‌شوید.")
                existing_report = StressTestReport.objects.get(
                    reception_service=reception_service)  # Uses GFK property directly
                return redirect(reverse('exercise_stress_test:stress_update', kwargs={'pk': existing_report.pk}))

            form.instance.reception_service = reception_service  # Set GFK
            form.instance.patient = reception_service.reception.patient  # Patient from ReceptionService
        else:
            # Handle creation for a patient without a specific ReceptionService
            patient_id = self.kwargs.get('patient_id')
            if patient_id:
                form.instance.patient = get_object_or_404(Patient, id=patient_id)
            else:
                messages.error(self.request, "برای ثبت گزارش تست ورزش، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                return redirect(reverse_lazy('exercise_stress_test:stress_test_worklist'))

        form.instance.created_by = self.request.user  # Set the user who created the report

        response = super().form_valid(form)  # Save the report instance

        # The StressTestReport.save() method now handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✅ گزارش تست ورزش / استرس اکو با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        # Redirect to the worklist or the detail page of the created report
        return reverse('exercise_stress_test:stress_detail', kwargs={'pk': self.object.pk})


class StressTestReportUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = StressTestReport
    form_class = StressTestReportForm
    template_name = 'exercise_stress_test/stress_test_form.html'  # Reusing the form template
    context_object_name = 'report'
    permission_required = 'exercise_stress_test.change_stresstestreport'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure patient and prescriptions are available for the form if needed
        context['patient'] = self.object.patient
        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient).order_by("-created_at")

        # Pass initial patient and service to form (for hidden/disabled fields)
        self.form_class.base_fields['patient'].initial = self.object.patient.pk
        self.form_class.base_fields['prescription'].queryset = Prescription.objects.filter(patient=self.object.patient)

        return context

    def form_valid(self, form):
        response = super().form_valid(form)  # Save the updated report instance

        # The StressTestReport.save() method handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✏️ گزارش تست ورزش / استرس اکو با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
        return reverse('exercise_stress_test:stress_detail', kwargs={'pk': self.object.pk})


class StressTestReportDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = StressTestReport
    template_name = 'exercise_stress_test/stress_test_confirm_delete.html'
    context_object_name = 'report'
    permission_required = 'exercise_stress_test.delete_stresstestreport'

    def get_success_url(self):
        # If a Stress Test report is deleted, you might want to revert the ReceptionService status
        messages.warning(self.request, "🗑️ گزارش تست ورزش / استرس اکو با موفقیت حذف شد.")
        return reverse_lazy('exercise_stress_test:stress_list')  # Redirect to the list view