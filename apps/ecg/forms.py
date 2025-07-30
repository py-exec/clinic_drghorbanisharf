# apps/ecg/forms.py

from django import forms
from .models import ECGRecord
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.contrib.auth import get_user_model

User = get_user_model()


class ECGRecordForm(forms.ModelForm):
    # Override fields to use specific widgets or modify properties
    exam_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="تاریخ و زمان معاینه",
        required=False  # Allow initial creation without immediate exam time
    )
    # Ensure foreign key fields use ModelChoiceField and have appropriate querysets
    prescription = forms.ModelChoiceField(
        queryset=Prescription.objects.all(),  # This should be filtered by patient in the view
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="نسخه مربوطه",
        required=False
    )
    technician = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Technicians').order_by('first_name', 'last_name'),
        # Assuming a 'Technicians' group
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="تکنسین ثبت‌کننده",
        required=False  # Can be set automatically by view if needed
    )
    reporting_physician = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Doctors').order_by('first_name', 'last_name'),
        # Assuming a 'Doctors' group
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="پزشک گزارش‌دهنده",
        required=False  # Can be set automatically by view if needed
    )

    # Boolean fields using CheckboxInput
    tech_issue = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="آیا مشکل تکنیکی وجود داشت؟",
        required=False
    )
    q_wave = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Q موج پاتولوژیک؟",
        required=False
    )
    u_wave = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="U موج مشاهده شد؟",
        required=False
    )
    ecg_repeat = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="نیاز به تکرار نوار؟",
        required=False
    )

    # NEW: tech_signature and doctor_signature as ModelChoiceField
    tech_signature = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name__in=['Technicians', 'Doctors']).order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="امضای تکنسین",
        required=False
    )
    doctor_signature = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Doctors').order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="امضای پزشک",
        required=False
    )

    class Meta:
        model = ECGRecord
        fields = [
            'prescription', 'exam_datetime', 'ecg_type', 'patient_position',
            'room_temp', 'ecg_location', 'ecg_quality', 'tech_issue', 'issue_desc',
            'device_serial', 'start_time', 'end_time', 'hr', 'rhythm', 'axis', 'qrs',
            'qtc', 'p_wave', 'st_t', 'q_wave', 'u_wave', 'tech_opinion', 'ecg_file',
            'ecg_repeat', 'repeat_reason', 'tech_signature', 'doctor_signature', 'ai_result'
        ]
        # Widgets for default fields
        widgets = {
            'ecg_type': forms.Select(attrs={'class': 'form-select'}),
            'patient_position': forms.TextInput(attrs={'class': 'form-control'}),
            'room_temp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'ecg_location': forms.TextInput(attrs={'class': 'form-control'}),
            'ecg_quality': forms.Select(attrs={'class': 'form-select'}),
            'issue_desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'device_serial': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'hr': forms.NumberInput(attrs={'class': 'form-control'}),
            'rhythm': forms.TextInput(attrs={'class': 'form-control'}),
            'axis': forms.TextInput(attrs={'class': 'form-control'}),
            'qrs': forms.TextInput(attrs={'class': 'form-control'}),
            'qtc': forms.TextInput(attrs={'class': 'form-control'}),
            'p_wave': forms.TextInput(attrs={'class': 'form-control'}),
            'st_t': forms.TextInput(attrs={'class': 'form-control'}),
            'tech_opinion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ecg_file': forms.FileInput(attrs={'class': 'form-control'}),
            'repeat_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'ai_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        # Labels for default fields (if not already handled by verbose_name in model)
        labels = {
            'ecg_type': 'نوع نوار',
            'patient_position': 'وضعیت بیمار هنگام ثبت',
            'room_temp': 'دمای اتاق',
            'ecg_location': 'محل انجام نوار',
            'ecg_quality': 'کیفیت نوار',
            'issue_desc': 'توضیح مشکل',
            'device_serial': 'شماره سریال دستگاه ECG',
            'hr': 'HR (ضربان)',
            'rhythm': 'ریتم غالب',
            'axis': 'محور قلب (Axis)',
            'qrs': 'QRS',
            'qtc': 'QTc',
            'p_wave': 'P موج',
            'st_t': 'ST-T تغییرات',
            'tech_opinion': 'توضیح تکنسین',
            'ecg_file': 'فایل نوار قلب',
            'repeat_reason': 'دلیل تکرار',
            'ai_result': 'نتیجه تحلیل سیستم هوشمند',
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)

        # Apply common form-control class to all fields except CheckboxInput
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                # Ensure attrs exists before updating
                if 'attrs' not in field.widget:
                    field.widget.attrs = {}
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
            # For select fields, add select2 class
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] += ' select2'

        # Filter prescriptions by patient if provided
        if patient:
            self.fields['prescription'].queryset = Prescription.objects.filter(patient=patient)

        # Initializing datetime-local fields correctly for existing instances
        if self.instance.pk:
            if self.instance.exam_datetime:
                self.fields['exam_datetime'].initial = self.instance.exam_datetime.isoformat(timespec='minutes')
            if self.instance.start_time:
                self.fields['start_time'].initial = self.instance.start_time.isoformat(timespec='minutes')
            if self.instance.end_time:
                self.fields['end_time'].initial = self.instance.end_time.isoformat(timespec='minutes')

# A helper function/filter might be needed in templates for ModelChoiceField labels
# For example, to filter prescriptions in the template, or pass filtered queryset from view