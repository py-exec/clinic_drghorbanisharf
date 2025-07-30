# apps/tilt/forms.py

from django import forms

from .models import TiltTestReport


class TiltTestReportForm(forms.ModelForm):
    """
    فرم برای ایجاد و ویرایش گزارش تست تیلت.
    """

    class Meta:
        model = TiltTestReport
        # فیلدهایی که توسط کاربر پر می‌شوند
        exclude = [
            'content_type',
            'object_id',
            'prescription',
            'created_by',
            'created_at',
            'patient',  # 👈 اضافه کن
        ]
        widgets = {
            'last_event_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'referral_reason': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'standing_symptoms': forms.TextInput(
                attrs={'placeholder': 'علائم را با کاما جدا کنید', 'class': 'form-control'}),
            'doctor_comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'had_syncope': forms.Select(attrs={'class': 'form-select'}),
            'bp_drop': forms.Select(attrs={'class': 'form-select'}),
            'referring_physician': forms.TextInput(attrs={'class': 'form-control'}),
            'prior_symptoms': forms.TextInput(attrs={'class': 'form-control'}),
            'hr_during_syncope': forms.NumberInput(attrs={'class': 'form-control'}),
            'symptom_onset_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'recovery_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'response_type': forms.TextInput(attrs={'class': 'form-control'}),
            'final_result': forms.TextInput(attrs={'class': 'form-control'}),
            'tilt_upload': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فیلدهای مربوط به GenericForeignKey و فیلدهای سیستمی
        # به صورت خودکار در View مدیریت می‌شوند و در فرم نیستند.
