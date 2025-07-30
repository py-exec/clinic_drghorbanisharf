# apps/exercise_stress_test/forms.py
from datetime import timezone

from django import forms
from .models import StressTestReport
from apps.patient.models import Patient  # برای فیلتر نسخه‌ها
from apps.prescriptions.models import Prescription  # برای فیلتر نسخه‌ها
from django.contrib.auth import get_user_model  # برای فیلدهای یوزر

User = get_user_model()

# گزینه‌های عمومی برای فیلدهای CharField با انتخاب محدود
BOOLEAN_CHOICES = [
    ('yes', 'بله'),
    ('no', 'خیر'),
    ('unknown', 'نامشخص'),
]

# گزینه‌های نمونه برای مقیاس بورگ
BORG_SCALE_CHOICES = [
    ('6', '6 - بدون تلاش'), ('7', '7 - بسیار بسیار سبک'), ('8', '8 - بسیار سبک'),
    ('9', '9 - سبک'), ('10', '10 - نسبتاً سبک'), ('11', '11 - کمی سخت'),
    ('12', '12 - سخت'), ('13', '13 - نسبتاً سخت'), ('14', '14 - سخت'),
    ('15', '15 - بسیار سخت'), ('16', '16 - بسیار بسیار سخت'), ('17', '17 - حداکثر'),
]

# گزینه‌های نمونه برای علائم (قابل توسعه)
SYMPTOM_CHOICES = [
    ('chest_pain', 'درد قفسه سینه'),
    ('dyspnea', 'تنگی نفس'),
    ('fatigue', 'خستگی'),
    ('dizziness', 'سرگیجه'),
    ('arrhythmia', 'آریتمی'),
    ('no_symptoms', 'بدون علامت'),
    ('other', 'سایر'),
]


class StressTestReportForm(forms.ModelForm):
    # فیلدهای خاص با ویجت‌ها و کوئری‌ست‌های سفارشی
    prescription = forms.ModelChoiceField(
        queryset=Prescription.objects.all(),  # در __init__ فیلتر می‌شود
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="نسخه",
        required=False
    )
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),  # در __init__ فیلتر می‌شود (مثلاً فقط Staff)
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        label="ایجادکننده",
        required=False
    )

    # برای JSONField ها (symptoms, recovery_symptoms)
    # از MultipleChoiceField برای انتخاب چندگانه استفاده می‌کنیم
    symptoms = forms.MultipleChoiceField(
        choices=SYMPTOM_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="علائم حین تست",
        required=False
    )
    recovery_symptoms = forms.MultipleChoiceField(
        choices=SYMPTOM_CHOICES,  # می‌تواند گزینه‌های متفاوتی داشته باشد
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="علائم در ریکاوری",
        required=False
    )

    class Meta:
        model = StressTestReport
        exclude = [
            'content_type',  # برای GenericForeignKey در View تنظیم می‌شود
            'object_id',  # برای GenericForeignKey در View تنظیم می‌شود
            'reception_service',  # برای GenericForeignKey در View تنظیم می‌شود
            'patient',  # بیمار در View تنظیم می‌شود
        ]
        widgets = {
            'exam_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'stress_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),  # TimeField
            'test_duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS', 'class': 'form-control'}),
            # DurationField - نمایش به صورت متن

            # فیلدهای CharField با گزینه‌های محدود
            'stress_type': forms.Select(attrs={'class': 'form-select'}),
            'stress_stop_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'stress_symptomatic': forms.Select(choices=BOOLEAN_CHOICES, attrs={'class': 'form-select'}),
            'borg_scale': forms.Select(choices=BORG_SCALE_CHOICES, attrs={'class': 'form-select'}),
            'bp_during_test': forms.TextInput(attrs={'class': 'form-control'}),
            'recovery_st_change': forms.TextInput(attrs={'class': 'form-control'}),
            'baseline_ecg': forms.TextInput(attrs={'class': 'form-control'}),
            'pretest_contra': forms.TextInput(attrs={'class': 'form-control'}),
            'arrhythmia_type': forms.TextInput(attrs={'class': 'form-control'}),
            'ecg_leads': forms.TextInput(attrs={'class': 'form-control'}),
            'rwma_severity': forms.TextInput(attrs={'class': 'form-control'}),
            'mr_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'image_saved': forms.Select(choices=BOOLEAN_CHOICES, attrs={'class': 'form-select'}),
            # فرض می‌کنیم 'بله'/'خیر' کافی است
            'final_diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
            'final_plan': forms.TextInput(attrs={'class': 'form-control'}),

            # فیلدهای متنی بزرگ
            'protocol': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'stress_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recovery_monitoring': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'pretest_medications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'ecg_changes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'rwma_walls': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'technical_issues': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'findings': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'doctor_opinion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'recommendation': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'final_comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),

            # فیلدهای عددی
            'stress_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'patient_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'mets': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'hr_rest': forms.NumberInput(attrs={'class': 'form-control'}),
            'hr_peak': forms.NumberInput(attrs={'class': 'form-control'}),
            'hr_peak_metric': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_hr': forms.NumberInput(attrs={'class': 'form-control'}),
            'target_hr': forms.NumberInput(attrs={'class': 'form-control'}),
            'sbp_rest': forms.NumberInput(attrs={'class': 'form-control'}),
            'sbp_peak': forms.NumberInput(attrs={'class': 'form-control'}),
            'sbp_peak_metric': forms.NumberInput(attrs={'class': 'form-control'}),
            'recovery_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'hr_recovery': forms.NumberInput(attrs={'class': 'form-control'}),
            'sbp_recovery': forms.NumberInput(attrs={'class': 'form-control'}),
            'ef_rest': forms.NumberInput(attrs={'class': 'form-control'}),
            'ef_post': forms.NumberInput(attrs={'class': 'form-control'}),
            'pretest_sbp': forms.NumberInput(attrs={'class': 'form-control'}),
            'pretest_dbp': forms.NumberInput(attrs={'class': 'form-control'}),

            # فیلدهای بولی
            'wall_motion_abnormalities': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ischemic_changes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'arrhythmia_occurred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            # فیلدهای فایل
            'stress_video': forms.FileInput(attrs={'class': 'form-control'}),
            'echo_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)

        # فیلتر نسخه‌ها بر اساس بیمار (اگر موجود باشد)
        if patient:
            self.fields['prescription'].queryset = Prescription.objects.filter(patient=patient).order_by("-created_at")
        else:
            # اگر بیمار مشخص نیست، queryset نسخه را خالی کن
            self.fields['prescription'].queryset = Prescription.objects.none()

        # کوئری‌ست برای created_by (مثلا فقط پرسنل)
        self.fields['created_by'].queryset = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')

        # تنظیم مقدار اولیه برای DateTimeField و TimeField
        if self.instance.pk:
            if self.instance.exam_datetime:
                self.fields['exam_datetime'].initial = self.instance.exam_datetime.isoformat(timespec='minutes')
            if self.instance.stress_start_time:
                self.fields['stress_start_time'].initial = self.instance.stress_start_time.isoformat(timespec='minutes')
            # DurationField (test_duration)
            if self.instance.test_duration:
                # Convert timedelta to string format HH:MM:SS for display
                total_seconds = int(self.instance.test_duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.fields['test_duration'].initial = f"{hours:02}:{minutes:02}:{seconds:02}"

        # برای JSONField‌ها که از MultipleChoiceField استفاده می‌کنند، باید داده‌های ذخیره شده را به فرمت لیست تبدیل کرد.
        if self.instance.pk:
            if self.instance.symptoms:
                self.fields['symptoms'].initial = self.instance.symptoms
            if self.instance.recovery_symptoms:
                self.fields['recovery_symptoms'].initial = self.instance.recovery_symptoms

    # ولیدیشن سفارشی برای JSONFieldها در زمان پاکسازی (clean)
    def clean_symptoms(self):
        symptoms = self.cleaned_data.get('symptoms')
        if symptoms is not None:
            # Django's MultipleChoiceField already returns a list, which is good for JSONField
            return symptoms
        return []  # Return empty list if no symptoms selected

    def clean_recovery_symptoms(self):
        recovery_symptoms = self.cleaned_data.get('recovery_symptoms')
        if recovery_symptoms is not None:
            return recovery_symptoms
        return []

    # ولیدیشن سفارشی برای DurationField اگر به صورت TextInput استفاده شود
    def clean_test_duration(self):
        duration_str = self.cleaned_data.get('test_duration')
        if duration_str:
            try:
                # Expected format HH:MM:SS
                h, m, s = map(int, duration_str.split(':'))
                return timezone.timedelta(hours=h, minutes=m, seconds=s)
            except ValueError:
                raise forms.ValidationError("فرمت مدت تست باید HH:MM:SS باشد.")
        return None