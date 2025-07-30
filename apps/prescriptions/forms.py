# apps/prescriptions/forms.py

from django import forms
from .models import (
    Prescription,
    PrescriptionMedication,
    TestRequest,
    DeviceAssessment,
    SurgeryPlan,
    TestStatus # Import TestStatus for choices
)
from apps.patient.models import Patient
from apps.doctors.models import Doctor
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory # For inline forms

User = get_user_model()

# --- فرم اصلی: PrescriptionForm ---
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        # فیلدهای GenericForeignKey (content_type, object_id, reception_service)
        # و patient, created_by در View تنظیم می‌شوند و نباید در فرم باشند.
        exclude = [
            'content_type',
            'object_id',
            'reception_service',
            'patient',
            'created_by',
            'created_at', # inherited from TimeStampedModel and set automatically
            'updated_at', # inherited from TimeStampedModel and set automatically
        ]
        widgets = {
            'symptom_onset': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'angiography_result': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'followup_plan': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'referral_specialist': forms.Select(attrs={'class': 'form-select'}),
            'final_doctor_note': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'review_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-select select2'}), # Предполагается, что Doctor ForeignKey
        }

    def __init__(self, *args, **kwargs):
        patient_instance = kwargs.pop('patient_instance', None) # برای فیلتر پزشکان و غیره
        super().__init__(*args, **kwargs)

        # فیلتر پزشکان (اگر نیاز باشد)
        self.fields['doctor'].queryset = Doctor.objects.all().order_by('full_name')

        # تنظیم کلاس form-control برای اکثر فیلدها
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect, forms.ClearableFileInput)):
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] += ' select2' # برای فعال کردن Select2

# --- فرم‌های Inline برای مدل‌های مرتبط ---

# PrescriptionMedicationForm
class PrescriptionMedicationForm(forms.ModelForm):
    class Meta:
        model = PrescriptionMedication
        fields = '__all__' # یا لیست فیلدهای مورد نظر
        exclude = ['prescription'] # این در formset به صورت خودکار تنظیم می‌شود
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dose': forms.TextInput(attrs={'class': 'form-control'}),
            'total': forms.NumberInput(attrs={'class': 'form-control'}),
            'per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'med_type': forms.Select(attrs={'class': 'form-select'}),
        }

# TestRequestForm
class TestRequestForm(forms.ModelForm):
    class Meta:
        model = TestRequest
        fields = '__all__'
        exclude = ['prescription']
        widgets = {
            'holter_ecg': forms.Select(attrs={'class': 'form-select'}),
            'holter_bp': forms.Select(attrs={'class': 'form-select'}),
            'tilt_test': forms.Select(attrs={'class': 'form-select'}),
            'stress_test': forms.Select(attrs={'class': 'form-select'}),
            'echo': forms.Select(attrs={'class': 'form-select'}),
            'tee': forms.Select(attrs={'class': 'form-select'}),
        }

# DeviceAssessmentForm
class DeviceAssessmentForm(forms.ModelForm):
    class Meta:
        model = DeviceAssessment
        fields = '__all__'
        exclude = ['prescription']
        widgets = {
            'device_type': forms.TextInput(attrs={'class': 'form-control'}),
            'battery_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'device_implant_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shock_occurred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lead_problem': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

# SurgeryPlanForm
class SurgeryPlanForm(forms.ModelForm):
    class Meta:
        model = SurgeryPlan
        fields = '__all__'
        exclude = ['prescription', 'created_by'] # created_by در View تنظیم می‌شود
        widgets = {
            'need_battery_replacement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'need_lead_revision': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'need_device_extraction': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'general_surgery_needed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'general_surgery_reason': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'suggested_surgery_type': forms.Select(attrs={'class': 'form-select'}),
            'suggested_surgery_note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'implant_location': forms.Select(attrs={'class': 'form-select'}),
            'implant_location_note': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'preferred_surgery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'surgery_center': forms.TextInput(attrs={'class': 'form-control'}),
            'surgeon_name': forms.TextInput(attrs={'class': 'form-control'}),
            'doctor_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

# --- Formset Factory برای مدیریت چندین داروی نسخه ---
PrescriptionMedicationFormSet = inlineformset_factory(
    Prescription,
    PrescriptionMedication,
    form=PrescriptionMedicationForm,
    extra=1, # تعداد فرم‌های خالی اولیه
    can_delete=True,
    fields='__all__'
)

# --- Formset Factory برای TestRequest (یک به یک، پس فقط یک extra=0 یا extra=1) ---
# برای OneToOneField، معمولاً extra=0 است و در صورت عدم وجود، ایجاد می‌شود.
TestRequestFormSet = inlineformset_factory(
    Prescription,
    TestRequest,
    form=TestRequestForm,
    extra=0, # برای OneToOneField، معمولاً 0 است، مگر اینکه بخواهید همیشه یک فرم خالی نمایش داده شود
    can_delete=False, # نباید بتوانید TestRequest اصلی را حذف کنید (فقط ویرایش)
    max_num=1 # برای OneToOneField، حداکثر 1
)

# --- Formset Factory برای DeviceAssessment ---
DeviceAssessmentFormSet = inlineformset_factory(
    Prescription,
    DeviceAssessment,
    form=DeviceAssessmentForm,
    extra=0, # برای OneToOneField
    can_delete=False,
    max_num=1
)

# --- Formset Factory برای SurgeryPlan ---
SurgeryPlanFormSet = inlineformset_factory(
    Prescription,
    SurgeryPlan,
    form=SurgeryPlanForm,
    extra=0, # برای OneToOneField
    can_delete=False,
    max_num=1
)