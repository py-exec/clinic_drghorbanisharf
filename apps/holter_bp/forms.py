# apps/holter_bp/forms.py

from django import forms

from .models import HolterBPInstallation, HolterBPReception, HolterBPReading


class HolterBPInstallationForm(forms.ModelForm):
    """
    فرم برای ثبت اطلاعات مرحله اول: نصب دستگاه هلتر.
    """

    class Meta:
        model = HolterBPInstallation
        exclude = [
            'content_type',
            'object_id',
            'patient',
            'tracking_code',
            'created_by',
        ]
        widgets = {
            'install_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'device': forms.Select(attrs={'class': 'form-select'}),
            'technician': forms.Select(attrs={'class': 'form-select'}),
            'patient_education_given': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class HolterBPReceptionForm(forms.ModelForm):
    """
    فرم برای ثبت اطلاعات مرحله دوم: دریافت دستگاه از بیمار.
    """

    class Meta:
        model = HolterBPReception
        exclude = ['installation']
        widgets = {
            'receive_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'received_by': forms.Select(attrs={'class': 'form-select'}),
            'device_condition_on_return': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'patient_feedback': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class HolterBPReadingForm(forms.ModelForm):
    """
    فرم برای ثبت اطلاعات مرحله سوم: خوانش و تحلیل گزارش.
    این نسخه شامل فیلدهای دقیق فشار خون است.
    """

    class Meta:
        model = HolterBPReading
        exclude = ['installation']
        fields = [
            'read_datetime',
            'interpreted_by',
            'avg_systolic_bp', 'min_systolic_bp', 'min_systolic_time', 'max_systolic_bp', 'max_systolic_time',
            'avg_diastolic_bp', 'min_diastolic_bp', 'min_diastolic_time', 'max_diastolic_bp', 'max_diastolic_time',
            'summary',
            'report_file',
            'notes',
        ]
        widgets = {
            'read_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'interpreted_by': forms.Select(attrs={'class': 'form-select'}),

            # ویجت‌های جدید برای فیلدهای فشار خون
            'avg_systolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'min_systolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'min_systolic_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'max_systolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'max_systolic_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),

            'avg_diastolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'min_diastolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'min_diastolic_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'max_diastolic_bp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'max_diastolic_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),

            'summary': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'report_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
