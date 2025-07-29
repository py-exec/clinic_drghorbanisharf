from django import forms

from .models import ServiceType, ServiceTariff
from apps.accounts.models import Role

class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = [
            "code", "name", "description", "is_active",
            "duration_minutes", "assigned_role", "model_path"  # ← جدید
        ]
        widgets = {
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "مثلاً ECG-01"
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "نام کامل خدمت مانند 'نوار قلب'"
            }),
            "description": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "توضیحات تکمیلی درباره این خدمت"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "duration_minutes": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "مثلاً 15"
            }),
            "assigned_role": forms.Select(attrs={
                "class": "form-select",
            }),
            "model_path": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "مثلاً apps.ecg.models.ECGRecord"
            }),
        }
        labels = {
            "code": "کد خدمت",
            "name": "نام خدمت",
            "description": "توضیحات",
            "is_active": "فعال؟",
            "duration_minutes": "مدت خدمت (دقیقه)",
            "assigned_role": "نقش مسئول خدمت",
            "model_path": "مسیر مدل رکورد تخصصی",  # ← جدید
        }

class ServiceTariffForm(forms.ModelForm):
    class Meta:
        model = ServiceTariff
        fields = ["service_type", "amount", "valid_from", "valid_to", "insurance_coverage"]
        widgets = {
            "service_type": forms.Select(attrs={
                "class": "form-select"
            }),
            "amount": forms.TextInput(attrs={
                "class": "form-control amount-input",
                "placeholder": "مثلاً ۱۵۰٬۰۰۰ تومان"
            }),
            "valid_from": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
                "placeholder": "تاریخ شروع اعتبار"
            }),
            "valid_to": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
                "placeholder": "تاریخ پایان اعتبار"
            }),
            "insurance_coverage": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0", "max": "100", "step": "0.1",
                "placeholder": "مثلاً 90 برای ۹۰٪"
            }),
        }
        labels = {
            "service_type": "نوع خدمت",
            "amount": "مبلغ (تومان)",
            "valid_from": "شروع اعتبار",
            "valid_to": "پایان اعتبار",
            "insurance_coverage": "پوشش بیمه‌ای (%)",
        }

    def clean_insurance_coverage(self):
        coverage = self.cleaned_data.get("insurance_coverage")
        if coverage is not None and not (0 <= coverage <= 100):
            raise forms.ValidationError("پوشش بیمه‌ای باید بین ۰ تا ۱۰۰ باشد.")
        return coverage
