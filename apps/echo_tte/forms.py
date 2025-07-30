# apps/echo_tte/forms.py

from django import forms
from .models import TTEEchoReport  # Import the TTEEchoReport model
from apps.patient.models import Patient  # Import Patient if needed for custom form logic
from apps.prescriptions.models import Prescription  # Import Prescription if needed for custom form logic
from django.contrib.auth import get_user_model  # Import User model

User = get_user_model()


class TTEEchoReportForm(forms.ModelForm):
    """
    فرم برای ایجاد و ویرایش گزارش اکوکاردیوگرافی از راه قفسه سینه (TTE).
    """

    class Meta:
        model = TTEEchoReport
        # فیلدهایی که نباید مستقیماً در فرم توسط کاربر تنظیم شوند:
        # - content_type, object_id: برای GenericForeignKey هستند و در View تنظیم می‌شوند.
        # - patient: معمولا از طریق URL یا View تنظیم می‌شود.
        # - created_by: کاربر ایجاد کننده است و در View تنظیم می‌شود.
        # - reception_service: GFK است و در View تنظیم می‌شود.
        exclude = [
            'content_type',
            'object_id',
            'reception_service',
            'patient',  # بیمار معمولاً از طریق View و URL مشخص می‌شود
            'created_by',  # کاربر ایجادکننده
        ]
        widgets = {
            'exam_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'prescription': forms.Select(attrs={'class': 'form-select'}),  # فرض می‌کنیم نسخه‌ها از قبل وجود دارند

            # عملکرد بطن چپ
            'ef': forms.TextInput(attrs={'class': 'form-control'}),
            'lv_dysfunction': forms.TextInput(attrs={'class': 'form-control'}),
            'lvedd': forms.TextInput(attrs={'class': 'form-control'}),
            'lvesd': forms.TextInput(attrs={'class': 'form-control'}),
            'gls': forms.TextInput(attrs={'class': 'form-control'}),
            'image_type': forms.TextInput(attrs={'class': 'form-control'}),

            # عملکرد بطن راست و فشار ریوی
            'tapse': forms.TextInput(attrs={'class': 'form-control'}),
            'spap': forms.TextInput(attrs={'class': 'form-control'}),
            'ivc_status': forms.TextInput(attrs={'class': 'form-control'}),

            # دریچه‌ها
            'mitral_type': forms.TextInput(attrs={'class': 'form-control'}),
            'mitral_severity': forms.TextInput(attrs={'class': 'form-control'}),
            'mitral_features': forms.TextInput(attrs={'class': 'form-control'}),

            'aortic_type': forms.TextInput(attrs={'class': 'form-control'}),
            'aortic_severity': forms.TextInput(attrs={'class': 'form-control'}),
            'aortic_features': forms.TextInput(attrs={'class': 'form-control'}),

            'tricuspid_type': forms.TextInput(attrs={'class': 'form-control'}),
            'tricuspid_severity': forms.TextInput(attrs={'class': 'form-control'}),

            'pulmonary_type': forms.TextInput(attrs={'class': 'form-control'}),
            'pulmonary_severity': forms.TextInput(attrs={'class': 'form-control'}),

            # یافته‌های دیگر
            'pericardial_effusion': forms.TextInput(attrs={'class': 'form-control'}),
            'pleural_effusion': forms.TextInput(attrs={'class': 'form-control'}),
            'mass_or_clot': forms.TextInput(attrs={'class': 'form-control'}),
            'aneurysm': forms.TextInput(attrs={'class': 'form-control'}),

            # کیفیت و شرایط تصویر
            'image_quality': forms.TextInput(attrs={'class': 'form-control'}),
            'image_limitation_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'probe_type': forms.TextInput(attrs={'class': 'form-control'}),
            'ecg_sync': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Changed from CharField to Boolean in model, assuming

            # اطلاعات تکنسین
            'patient_cooperation': forms.TextInput(attrs={'class': 'form-control'}),
            'all_views_taken': forms.TextInput(attrs={'class': 'form-control'}),
            # Changed from CharField to Boolean in model, assuming
            'technician': forms.Select(attrs={'class': 'form-select'}),  # از ForeignKey به User استفاده می‌کند
            'technician_note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),

            # نظر نهایی پزشک
            'need_advanced_echo': forms.TextInput(attrs={'class': 'form-control'}),
            'reason_advanced_echo': forms.TextInput(attrs={'class': 'form-control'}),
            'reporting_physician': forms.Select(attrs={'class': 'form-select'}),  # از ForeignKey به User استفاده می‌کند
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'final_report': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),

            # فایل پیوست
            'upload_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اگر می‌خواهید کوئری‌ست نسخه‌ها را برای بیمار فعلی فیلتر کنید
        # این کار معمولا در View انجام می‌شود، نه در Form.__init__
        # مگر اینکه فرم را به گونه‌ای بسازید که patient را از context دریافت کند.
        # اما برای سادگی، فعلا همه نسخه‌ها را نشان می‌دهد، یا در View فیلتر می‌شود.

        # اگر لازم بود فقط پزشکان را در Select Technician/Reporting Physician نمایش دهد
        # self.fields['technician'].queryset = User.objects.filter(groups__name='Technician')
        # self.fields['reporting_physician'].queryset = User.objects.filter(groups__name='Doctor')