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
from django.db.models import Subquery, OuterRef, F, Count
from django.utils import timezone  # Make sure timezone is imported
from django.db import transaction  # For atomic transactions with formsets

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
from apps.patient.models import Patient  # Needed for patient context
from apps.doctors.models import Doctor  # Needed for doctor context


# --- Views for managing Prescriptions ---

class PrescriptionListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = Prescription
    template_name = "prescriptions/prescription_list.html"  # New template name
    context_object_name = "prescriptions"
    paginate_by = 15  # Add pagination
    permission_required = "prescriptions.view_prescription"  # Adjust permission as needed

    def get_queryset(self):
        # Prefetch related data for efficiency
        return Prescription.objects.select_related(
            "patient", "created_by", "doctor"
        ).order_by("-created_at")


# Note: doctor_review_list is now PrescriptionListView


class PrescriptionDetailView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = Prescription
    template_name = "prescriptions/prescription_detail.html"  # New template name
    context_object_name = "prescription"
    permission_required = "prescriptions.view_prescription"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add formsets for displaying existing related data
        context['medication_formset'] = PrescriptionMedicationFormSet(instance=self.object)
        context['test_request_form'] = TestRequestFormSet(instance=self.object)  # It's a formset, but max_num=1
        context['device_assessment_form'] = DeviceAssessmentFormSet(instance=self.object)
        context['surgery_plan_form'] = SurgeryPlanFormSet(instance=self.object)
        return context


# Note: doctor_review_detail is now PrescriptionDetailView


class PrescriptionCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "prescriptions/prescription_form.html"  # New template name
    permission_required = "prescriptions.add_prescription"  # Adjust permission as needed

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')  # From URL: create/for-patient/<int:patient_id>/
        service_id = self.kwargs.get('service_id')  # From URL: create/for-service/<int:service_id>/

        patient = None
        service = None

        if patient_id:
            patient = get_object_or_404(Patient, pk=patient_id)
        elif service_id:
            service = get_object_or_404(ReceptionService, pk=service_id)
            patient = service.reception.patient  # Get patient from ReceptionService

        if not patient:
            messages.error(self.request, "برای ثبت نسخه، بیمار باید مشخص باشد.")
            return redirect(reverse_lazy('patient:patient_list'))  # Redirect to patient list if no patient found

        context['patient'] = patient
        context['service'] = service

        # Instantiate formsets for initial display (empty forms for new creation)
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

        # Pass patient instance to form for queryset filtering in __init__
        context['form'] = self.form_class(patient_instance=patient,
                                          initial={'patient': patient})  # Pass patient to form
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

        with transaction.atomic():  # Ensure all saves are atomic
            form.instance.patient = patient
            form.instance.created_by = self.request.user  # Set user who created the prescription
            if service:
                form.instance.reception_service = service  # Link to ReceptionService if applicable

            self.object = form.save()  # Save the main Prescription instance

            # Save formsets
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
                # If formsets are not valid, re-render the form with errors
                # This requires returning to the template with the invalid formsets
                messages.error(self.request, "❌ خطاهایی در فرم‌های مرتبط وجود دارد. لطفاً اصلاح کنید.")
                return self.form_invalid(form)  # Re-render the form with main form errors

    def form_invalid(self, form):
        # Re-populate formsets on invalid submission
        context = self.get_context_data(form=form)
        context['medication_formset'] = PrescriptionMedicationFormSet(self.request.POST, instance=form.instance)
        context['test_request_form'] = TestRequestFormSet(self.request.POST, instance=form.instance)
        context['device_assessment_form'] = DeviceAssessmentFormSet(self.request.POST, instance=form.instance)
        context['surgery_plan_form'] = SurgeryPlanFormSet(self.request.POST, instance=form.instance)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('prescriptions:prescription_detail', kwargs={'pk': self.object.pk})


# Note: doctor_review_create is now PrescriptionCreateView


class PrescriptionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "prescriptions/prescription_form.html"  # Reusing the form template
    context_object_name = "prescription"
    permission_required = "prescriptions.change_prescription"  # Adjust permission as needed

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass patient instance to form for queryset filtering in __init__
        context['form'] = self.form_class(instance=self.object, patient_instance=self.object.patient)

        # Instantiate formsets for existing data
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

        context['patient'] = self.object.patient  # Pass patient for display in template
        return context

    def form_valid(self, form):
        with transaction.atomic():  # Ensure all saves are atomic
            self.object = form.save()  # Save the main Prescription instance

            # Save formsets
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
                return self.form_invalid(form)  # Re-render the form with errors

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['medication_formset'] = PrescriptionMedicationFormSet(self.request.POST, instance=form.instance)
        context['test_request_form'] = TestRequestFormSet(self.request.POST, instance=form.instance)
        context['device_assessment_form'] = DeviceAssessmentFormSet(self.request.POST, instance=form.instance)
        context['surgery_plan_form'] = SurgeryPlanFormSet(self.request.POST, instance=form.instance)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('prescriptions:prescription_detail', kwargs={'pk': self.object.pk})


# Note: doctor_review_update is now PrescriptionUpdateView


class PrescriptionDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Prescription
    template_name = "prescriptions/prescription_confirm_delete.html"  # New template name
    context_object_name = "prescription"
    permission_required = "prescriptions.delete_prescription"  # Adjust permission as needed

    def get_success_url(self):
        messages.warning(self.request, "🗑️ نسخه با موفقیت حذف شد.")
        return reverse_lazy('prescriptions:prescription_list')  # Redirect to the list view

# Note: doctor_review_delete is now PrescriptionDeleteView