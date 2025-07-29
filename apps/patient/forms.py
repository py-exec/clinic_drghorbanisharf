from apps.accounts.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from .models import Patient


class PatientLookupForm(forms.Form):
    query = forms.CharField(
        label="کد ملی یا شماره موبایل بیمار",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': 'کد ملی یا شماره موبایل را وارد کنید...'
        })
    )


class PatientUserForm(forms.ModelForm):
    # --- فیلدهای User ---
    first_name = forms.CharField(label="نام", max_length=50)
    last_name = forms.CharField(label="نام خانوادگی", max_length=50)
    national_code = forms.CharField(label="کد ملی", max_length=10)
    phone_number = forms.CharField(label="شماره موبایل", max_length=15)
    email = forms.EmailField(label="ایمیل", required=False)

    class Meta:
        model = Patient
        fields = [
            # اطلاعات پزشکی
            'blood_group', 'has_allergy', 'allergy_info', 'chronic_diseases',
            'heart_surgery', 'surgery_description', 'mobility_status',
            'special_needs', 'health_literacy', 'blood_sugar_status',

            # بیمه پایه
            'basic_insurance_company', 'basic_insurance_number', 'basic_insurance_file',

            # بیمه تکمیلی
            'supplementary_insurance_company', 'supplementary_insurance_number', 'supplementary_insurance_file',

            # ارجاع
            'is_referred', 'referring_doctor', 'referring_center', 'referral_file',

            # همراه
            'companion_name', 'companion_relation', 'companion_phone', 'companion_decision',
        ]

        widgets = {
            'allergy_info': forms.Textarea(attrs={'rows': 2}),
            'surgery_description': forms.Textarea(attrs={'rows': 2}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'chronic_diseases': forms.Select(attrs={'class': 'form-select'}),
            'mobility_status': forms.Select(attrs={'class': 'form-select'}),
            'health_literacy': forms.Select(attrs={'class': 'form-select'}),
            'blood_sugar_status': forms.Select(attrs={'class': 'form-select'}),
            'basic_insurance_company': forms.Select(attrs={'class': 'form-select'}),
            'supplementary_insurance_company': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.user:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['national_code'].initial = user.national_code
            self.fields['phone_number'].initial = user.phone_number
            self.fields['email'].initial = user.email

            self.fields['national_code'].readonly = True
            self.fields['phone_number'].readonly = True

    @transaction.atomic
    def save(self, commit=True):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        national_code = self.cleaned_data.get('national_code')
        phone_number = self.cleaned_data.get('phone_number')
        email = self.cleaned_data.get('email')

        if self.instance and self.instance.pk and self.instance.user:
            user = self.instance.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
        else:
            existing_user = User.objects.filter(
                Q(national_code=national_code) | Q(phone_number=phone_number)
            ).first()

            if existing_user:
                if Patient.objects.filter(user=existing_user).exists():
                    self.add_error('national_code', 'بیماری با این مشخصات قبلاً به طور کامل ثبت‌نام شده است.')
                    raise ValidationError("بیمار تکراری است.")
                else:
                    user = existing_user
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.save()
            else:
                user = User.objects.create_user(
                    username=phone_number,
                    phone_number=phone_number,
                    national_code=national_code,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=None
                )
            self.instance.user = user

        return super().save(commit=commit)
