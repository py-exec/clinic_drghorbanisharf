# apps/holter_hr/forms.py

from django import forms

from .models import HolterHRInstallation, HolterHRReception, HolterHRReading


class HolterHRInstallationForm(forms.ModelForm):
    """
    فرم برای ثبت اطلاعات مرحله اول: نصب دستگاه هلتر ضربان.
    """

    class Meta:
        model = HolterHRInstallation
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


class HolterHRReceptionForm(forms.ModelForm):
    """
    فرم برای ثبت اطلاعات مرحله دوم: دریافت دستگاه از بیمار.
    """

    class Meta:
        model = HolterHRReception
        exclude = ['installation']
        widgets = {
            'receive_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'received_by': forms.Select(attrs={'class': 'form-select'}),
            'device_condition_on_return': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'patient_feedback': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class HolterHRReadingForm(forms.ModelForm):
    """
    فرم برای ثبت اطلاعات مرحله سوم: خوانش و تحلیل گزارش.
    """

    class Meta:
        model = HolterHRReading
        exclude = ['installation']
        widgets = {
            'read_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'interpreted_by': forms.Select(attrs={'class': 'form-select'}),

            # ویجت‌های جدید برای فیلدهای ضربان قلب
            'avg_heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'bpm'}),
            'min_heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'bpm'}),
            'min_hr_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'max_heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'bpm'}),
            'max_hr_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),

            # HRV metrics
            'sdnn': forms.NumberInput(attrs={'class': 'form-control'}),
            'rmssd': forms.NumberInput(attrs={'class': 'form-control'}),
            'pnn50': forms.NumberInput(attrs={'class': 'form-control'}),

            'summary': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'report_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
