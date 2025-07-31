# apps/prescriptions/views.py

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
from django.db.models import Subquery, OuterRef, F, Count, Q
from django.utils import timezone
from django.db import transaction

# Import your models and forms
from .models import (
    Prescription,
    PrescriptionMedication,
    TestRequest,
    DeviceAssessment,
    SurgeryPlan,
)
from .forms import (
    PrescriptionForm,
    PrescriptionMedicationFormSet,
    TestRequestFormSet,
    DeviceAssessmentFormSet,
    SurgeryPlanFormSet,
)
from apps.patient.models import Patient
from apps.doctors.models import Doctor


# --- NEW: Dashboard View for Prescriptions ---
@login_required
@permission_required("prescriptions.view_prescription", raise_exception=True)
def prescriptions_dashboard_view(request):
    """
    داشبورد آماری برای نسخه‌ها و نظرات پزشک.
    """
    today = timezone.now().date()

    # Calculate statistics for prescriptions
    total_prescriptions_today = Prescription.objects.filter(created_at__date=today).count()
    total_prescriptions_this_week = Prescription.objects.filter(
        created_at__week_day__gte=today.weekday(),  # Starting from Monday or Sunday depending on locale
        created_at__date__lte=today  # Up to today
    ).count()

    # Example: Prescriptions with final doctor note (considered 'finalized')
    finalized_prescriptions_today = Prescription.objects.filter(
        created_at__date=today,
        final_doctor_note__isnull=False
    ).count()

    # Example: Prescriptions needing review (e.g., review_date is in future or not set)
    pending_review_prescriptions = Prescription.objects.filter(
        Q(review_date__isnull=True) | Q(review_date__gte=today)
    ).count()

    # If you want to integrate with TestRequest counts, it becomes more complex
    # as TestRequest is a OneToOneField on Prescription.
    # For now, let's keep it focused on Prescription itself.

    context = {
        'total_prescriptions_today': total_prescriptions_today,
        'finalized_prescriptions_today': finalized_prescriptions_today,
        'pending_review_prescriptions': pending_review_prescriptions,
        # Add more statistics as needed
    }
    return render(request, 'prescriptions/prescriptions_dashboard.html', context)


# --- Views for managing Prescriptions (Existing from previous step) ---

class PrescriptionListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = Prescription
    template_name = "prescriptions/prescription_list.html"
    context_object_name = "prescriptions"
    paginate_by = 15
    permission_required = "prescriptions.view_prescription"

    def get_queryset(self):
        return Prescription.objects.select_related(
            "patient", "created_by", "doctor"
        ).order_by("-created_at")


class PrescriptionDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Prescription
    template_name = "prescriptions/prescription_detail.html"
    context_object_name = "prescription"
    permission_required = "prescriptions.view_prescription"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medication_formset'] = PrescriptionMedicationFormSet(instance=self.object)
        context['test_request_form'] = TestRequestFormSet(instance=self.object)
        context['device_assessment_form'] = DeviceAssessmentFormSet(instance=self.object)
        context['surgery_plan_form'] = SurgeryPlanFormSet(instance=self.object)
        return context


class PrescriptionCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "prescriptions/prescription_form.html"
    permission_required = "prescriptions.add_prescription"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')
        service_id = self.kwargs.get('service_id')

        patient = None
        service = None

        if patient_id:
            patient = get_object_or_404(Patient, pk=patient_id)
        elif service_id:
            service = get_object_or_404(ReceptionService, pk=service_id)
            patient = service.reception.patient

        if not patient:
            messages.error(self.request, "برای ثبت نسخه، بیمار باید مشخص باشد.")
            return redirect(reverse_lazy('patient:patient_list'))

        context['patient'] = patient
        context['service'] = service

        if self.request.POST:
            context['medication_formset'] = PrescriptionMedicationFormSet(self.request.POST, instance=self.object)
            context['test_request_form'] = TestRequestFormSet(self.request.POST, instance=self.object)
            context['device_assessment_form'] = DeviceAssessmentFormSet(self.request.POST, instance=self.object)
            context['surgery_plan_form'] = SurgeryPlanFormSet(self.request.POST, instance=self.object)
        else:
            context['medication_formset'] = PrescriptionMedicationFormSet(instance=self.object)
            context['test_request_form'] = TestRequestFormSet(instance=self.object)
            context['device_assessment_form'] = DeviceAssessmentFormSet(instance=self.object)
            context['surgery_plan_form'] = SurgeryPlanFormSet(instance=self.object)

        context['form'] = self.form_class(patient_instance=patient, initial={'patient': patient})
        return context

    def form_valid(self, form):
        patient_id = self.kwargs.get('patient_id')
        service_id = self.kwargs.get('service_id')

        patient = None
        service = None

        if patient_id:
            patient = get_object_or_404(Patient, pk=patient_id)
        elif service_id:
            service = get_object_or_404(ReceptionService, pk=service_id)
            patient = service.reception.patient

        if not patient:
            messages.error(self.request, "برای ثبت نسخه، بیمار باید مشخص باشد.")
            return redirect(reverse_lazy('patient:patient_list'))

        with transaction.atomic():
            form.instance.patient = patient
            form.instance.created_by = self.request.user
            if service:
                form.instance.reception_service = service

            self.object = form.save()

            medication_formset = PrescriptionMedicationFormSet(self.request.POST, instance=self.object)
            test_request_form = TestRequestFormSet(self.request.POST, instance=self.object)
            device_assessment_form = DeviceAssessmentFormSet(self.request.POST, instance=self.object)
            surgery_plan_form = SurgeryPlanFormSet(self.request.POST, instance=self.object)

            formsets_valid = (
                    medication_formset.is_valid() and
                    test_request_form.is_valid() and
                    device_assessment_form.is_valid() and
                    surgery_plan_form.is_valid()
            )

            if formsets_valid:
                medication_formset.save()
                test_request_form.save()
                device_assessment_form.save()
                surgery_plan_form.save()
                messages.success(self.request, "✅ نسخه و اطلاعات مرتبط با موفقیت ثبت شد.")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, "❌ خطاهایی در فرم‌های مرتبط وجود دارد. لطفاً اصلاح کنید.")
                return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['medication_formset'] = PrescriptionMedicationFormSet(self.request.POST, instance=form.instance)
        context['test_request_form'] = TestRequestFormSet(self.request.POST, instance=form.instance)
        context['device_assessment_form'] = DeviceAssessmentFormSet(self.request.POST, instance=form.instance)
        context['surgery_plan_form'] = SurgeryPlanFormSet(self.request.POST, instance=form.instance)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('prescriptions:prescription_detail', kwargs={'pk': self.object.pk})


class PrescriptionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "prescriptions/prescription_form.html"
    context_object_name = "prescription"
    permission_required = "prescriptions.change_prescription"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object, patient_instance=self.object.patient)

        if self.request.POST:
            context['medication_formset'] = PrescriptionMedicationFormSet(self.request.POST, instance=self.object)
            context['test_request_form'] = TestRequestFormSet(self.request.POST, instance=self.object)
            context['device_assessment_form'] = DeviceAssessmentFormSet(self.request.POST, instance=self.object)
            context['surgery_plan_form'] = SurgeryPlanFormSet(self.request.POST, instance=self.object)
        else:
            context['medication_formset'] = PrescriptionMedicationFormSet(instance=self.object)
            context['test_request_form'] = TestRequestFormSet(instance=self.object)
            context['device_assessment_form'] = DeviceAssessmentFormSet(instance=self.object)
            context['surgery_plan_form'] = SurgeryPlanFormSet(instance=self.object)

        context['patient'] = self.object.patient
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

            medication_formset = PrescriptionMedicationFormSet(self.request.POST, instance=self.object)
            test_request_form = TestRequestFormSet(self.request.POST, instance=self.object)
            device_assessment_form = DeviceAssessmentFormSet(self.request.POST, instance=self.object)
            surgery_plan_form = SurgeryPlanFormSet(self.request.POST, instance=self.object)

            formsets_valid = (
                    medication_formset.is_valid() and
                    test_request_form.is_valid() and
                    device_assessment_form.is_valid() and
                    surgery_plan_form.is_valid()
            )

            if formsets_valid:
                medication_formset.save()
                test_request_form.save()
                device_assessment_form.save()
                surgery_plan_form.save()
                messages.success(self.request, "✏️ نسخه و اطلاعات مرتبط با موفقیت ویرایش شد.")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, "❌ خطاهایی در فرم‌های مرتبط وجود دارد. لطفاً اصلاح کنید.")
                return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['medication_formset'] = PrescriptionMedicationFormSet(self.request.POST, instance=form.instance)
        context['test_request_form'] = TestRequestFormSet(self.request.POST, instance=form.instance)
        context['device_assessment_form'] = DeviceAssessmentFormSet(self.request.POST, instance=form.instance)
        context['surgery_plan_form'] = SurgeryPlanFormSet(self.request.POST, instance=form.instance)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('prescriptions:prescription_detail', kwargs={'pk': self.object.pk})


class PrescriptionDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Prescription
    template_name = "prescriptions/prescription_confirm_delete.html"
    context_object_name = "prescription"
    permission_required = "prescriptions.delete_prescription"

    def get_success_url(self):
        messages.warning(self.request, "🗑️ نسخه با موفقیت حذف شد.")
        return reverse_lazy('prescriptions:prescription_list')