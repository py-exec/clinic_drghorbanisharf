# apps/ecg/views.py

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.template.loader import render_to_string

from apps.reception.models import ReceptionService, ServiceType, ReceptionServiceStatus
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models.expressions import Exists  # Make sure this is imported
from django.db.models import Subquery, OuterRef, F, Count
from django.utils import timezone

# Import your models and form
from .models import ECGRecord
from .forms import ECGRecordForm
from ..patient.models import Patient
from ..prescriptions.models import Prescription


# --- Worklist and List Views ---

@login_required
@permission_required("ecg.view_ecgrecord", raise_exception=True)
def ecg_worklist_view(request):
    """
    داشبورد کاری نوار قلب (ECG).
    نمایش بیماران در صف انتظار برای انجام ECG.
    """
    today = timezone.now().date()

    # Subquery برای گرفتن آخرین وضعیت هر ReceptionService
    latest_service_status_subquery = Subquery(
        ReceptionServiceStatus.objects.filter(
            reception_service=OuterRef('pk')
        ).order_by('-timestamp').values('status')[:1]
    )

    # Get the ServiceType object for ECG (using the code 'ECG')
    ecg_service_type = None
    try:
        ecg_service_type = ServiceType.objects.get(code='ECG')  # Assuming 'ECG' is the code for ECG
    except ServiceType.DoesNotExist:
        messages.error(request, "نوع خدمت 'نوار قلب (ECG)' (کد ECG) در سیستم یافت نشد. لطفاً آن را ایجاد کنید.")
        context = {
            'waiting_for_ecg_list': [],
            'done_today': 0,
            'in_queue_total': 0,
        }
        return render(request, 'ecg/ecg_worklist.html', context)

    # Base query for all ECG services for today, with latest ReceptionService status
    # ECG is a single-stage service, so we mostly care about its ReceptionService status
    ecg_relevant_reception_services = ReceptionService.objects.filter(
        tariff__service_type=ecg_service_type,  # Filter by the correct service type ('ECG')
        created_at__date=today,  # Services created today
    ).annotate(
        latest_service_status=latest_service_status_subquery
    ).select_related(
        'reception__patient__user', 'tariff__service_type'
    )

    # Check existence of ECGRecord for each ReceptionService
    reception_service_content_type = ContentType.objects.get_for_model(ReceptionService)
    has_ecg_report_qs = Exists(
        ECGRecord.objects.filter(
            content_type=reception_service_content_type,  # CORRECTED: Changed from reception_service_content_type
            object_id=OuterRef('pk')  # CORRECTED: Changed from reception_service_object_id
        )
    )

    # Annotate relevant ReceptionServices with the existence flag
    ecg_reception_services_annotated = ecg_relevant_reception_services.annotate(
        _has_report=has_ecg_report_qs,
    )

    # 1. لیست انتظار ECG (ReceptionServices that need an ECGRecord)
    waiting_for_ecg_list = ecg_reception_services_annotated.filter(
        latest_service_status__in=['pending', 'started', 'in_progress'],
        # Or whatever statuses mean 'not completed yet'
        _has_report=False  # Only services without a final ECG Record yet
    ).order_by('created_at')

    # Calculate Dashboard Stats
    done_today = ecg_reception_services_annotated.filter(latest_service_status='completed').count()
    in_queue_total = waiting_for_ecg_list.count()  # For single-stage, this is often just the main queue count

    context = {
        'waiting_for_ecg_list': waiting_for_ecg_list,
        'done_today': done_today,
        'in_queue_total': in_queue_total,
    }
    return render(request, 'ecg/ecg_worklist.html', context)


class ECGRecordListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = ECGRecord
    template_name = 'ecg/ecg_list.html'
    context_object_name = 'reports'
    paginate_by = 15  # Add pagination
    permission_required = "ecg.view_ecgrecord"

    def get_queryset(self):
        # Prefetch related data for efficiency
        return ECGRecord.objects.select_related(
            "patient", "prescription", "tech_signature", "doctor_signature"  # Use new FK names
        ).order_by("-created_at")


class ECGRecordDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = ECGRecord
    template_name = 'ecg/ecg_detail.html'
    context_object_name = 'report'
    permission_required = "ecg.view_ecgrecord"


class ECGRecordCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ECGRecord
    form_class = ECGRecordForm
    template_name = 'ecg/ecg_form.html'
    permission_required = 'ecg.add_ecgrecord'

    def get_initial(self):
        initial = super().get_initial()
        # Set created_by and default exam_datetime to current user and current time
        initial['created_by'] = self.request.user
        initial['exam_datetime'] = timezone.now()
        # technician and doctor signatures might also default to current user
        # initial['tech_signature'] = self.request.user
        # initial['doctor_signature'] = self.request.user
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
        else:
            # Handle case where report is created directly for a patient (not via service ID)
            patient_id = self.kwargs.get('patient_id')  # If URL is /create/for-patient/<int:patient_id>/
            if patient_id:
                patient = get_object_or_404(Patient, id=patient_id)
                context['patient'] = patient
                context['prescriptions'] = Prescription.objects.filter(patient=patient).order_by("-created_at")
            else:
                messages.warning(self.request, "برای ثبت گزارش ECG، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                return redirect(reverse_lazy('ecg:ecg_worklist'))
        return context

    def form_valid(self, form):
        service_id = self.kwargs.get('service_id')
        if service_id:
            reception_service = get_object_or_404(ReceptionService, pk=service_id)
            # Check if a report already exists for this service
            if ECGRecord.objects.filter(reception_service=reception_service).exists():  # Uses GFK property directly
                messages.warning(self.request,
                                 "برای این خدمت، قبلاً گزارش ECG ثبت شده است. به صفحه ویرایش هدایت می‌شوید.")
                existing_report = ECGRecord.objects.get(
                    reception_service=reception_service)  # Uses GFK property directly
                return redirect(reverse('ecg:ecg_update', kwargs={'pk': existing_report.pk}))

            form.instance.reception_service = reception_service  # Set GFK
            form.instance.patient = reception_service.reception.patient  # Patient from ReceptionService
        else:
            # Handle creation for a patient without a specific ReceptionService
            patient_id = self.kwargs.get('patient_id')
            if patient_id:
                form.instance.patient = get_object_or_404(Patient, id=patient_id)
            else:
                messages.error(self.request, "برای ثبت گزارش ECG، بیمار یا خدمت پذیرش شده باید مشخص باشد.")
                return redirect(reverse_lazy('ecg:ecg_worklist'))

        form.instance.created_by = self.request.user  # Set the user who created the report

        response = super().form_valid(form)  # Save the report instance

        # The ECGRecord.save() method now handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✅ گزارش نوار قلب (ECG) با موفقیت ثبت شد.")
        return response

    def get_success_url(self):
        # Redirect to the worklist or the detail page of the created report
        return reverse('ecg:ecg_detail', kwargs={'pk': self.object.pk})


class ECGRecordUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = ECGRecord
    form_class = ECGRecordForm
    template_name = 'ecg/ecg_form.html'  # Reusing the form template
    context_object_name = 'report'
    permission_required = 'ecg.change_ecgrecord'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure patient and prescriptions are available for the form if needed
        context['patient'] = self.object.patient
        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient).order_by("-created_at")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)  # Save the updated report instance

        # The ECGRecord.save() method handles calling change_service_status
        # if self.object.reception_service is set.

        messages.success(self.request, "✏️ گزارش نوار قلب (ECG) با موفقیت ویرایش شد.")
        return response

    def get_success_url(self):
        return reverse('ecg:ecg_detail', kwargs={'pk': self.object.pk})


class ECGRecordDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = ECGRecord
    template_name = 'ecg/ecg_confirm_delete.html'
    context_object_name = 'report'
    permission_required = 'ecg.delete_ecgrecord'

    def get_success_url(self):
        # If an ECG report is deleted, you might want to revert the ReceptionService status
        messages.warning(self.request, "🗑️ گزارش نوار قلب (ECG) با موفقیت حذف شد.")
        return reverse_lazy('ecg:ecg_list')  # Redirect to the list view


# Helper function ecg_table_partial (remains a function-based view, but uses select_related)
@login_required
@permission_required("ecg.view_ecgrecord", raise_exception=True)  # Add permission check
def ecg_table_partial(request):
    reports = ECGRecord.objects.select_related("patient", "prescription", "tech_signature",
                                               "doctor_signature").order_by("-created_at")
    html = render_to_string("ecg/partials/_ecg_table.html", {"reports": reports})
    return JsonResponse({"html": html})