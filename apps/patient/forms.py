# apps/patient/forms.py
from apps.accounts.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from .models import Patient

# Import for Jalali Dates (assuming django-jalali is installed and configured)
# If not using django-jalali, you'll need a custom date widget/field or to handle conversions manually.
try:
    from jalali_date.fields import JalaliDateField, JalaliSplitDateTimeField
    from jalali_date.widgets import AdminJalaliDateWidget, AdminJalaliDateTimeWidget
except ImportError:
    # Fallback if django-jalali is not installed
    JalaliDateField = forms.DateField
    AdminJalaliDateWidget = forms.DateInput
    print("Warning: django-jalali not found. Falling back to default DateField/DateInput.")


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
    # --- فیلدهای User که می‌خواهیم در فرم نمایش دهیم و ویرایش کنیم ---
    first_name = forms.CharField(label="نام", max_length=50)
    last_name = forms.CharField(label="نام خانوادگی", max_length=50)
    national_code = forms.CharField(label="کد ملی", max_length=10)
    phone_number = forms.CharField(label="شماره موبایل", max_length=15)
    email = forms.EmailField(label="ایمیل", required=False)

    # تاریخ تولد شمسی
    # فرض می‌کنیم فیلد date_of_birth در مدل User وجود دارد و از نوع DateField است.
    date_of_birth = JalaliDateField(
        label="تاریخ تولد (شمسی)",
        widget=AdminJalaliDateWidget, # یا هر ویجت شمسی دیگر
        required=False, # اگر date_of_birth در User الزامی نیست
    )

    # اگر فیلد جنسیت در مدل Patient وجود ندارد و می‌خواهید آن را از User بگیرید یا به User اضافه کنید
    # اگر در User است:
    gender = forms.ChoiceField(
        label="جنسیت",
        choices=User.GENDER_CHOICES if hasattr(User, 'GENDER_CHOICES') else [('', 'انتخاب کنید...'), ('male', 'مرد'), ('female', 'زن'), ('other', 'سایر')],
        required=False,
    )
    # توجه: اگر GENDER_CHOICES در User.py شما تعریف نشده، باید آن را اضافه کنید
    # یا از CHOICES مشترک پروژه یا یک CHOICES عمومی استفاده کنید.


    class Meta:
        model = Patient
        fields = [
            # اطلاعات پزشکی (فقط فیلدهایی که در مدل Patient باقی مانده‌اند)
            'blood_group', 'has_allergy', 'allergy_info',
            'mobility_status', 'special_needs', 'health_literacy',

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
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'mobility_status': forms.Select(attrs={'class': 'form-select'}),
            'health_literacy': forms.Select(attrs={'class': 'form-select'}),
            'basic_insurance_company': forms.Select(attrs={'class': 'form-select'}),
            'supplementary_insurance_company': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # مقداردهی اولیه فیلدهای User
        if self.instance and self.instance.pk and self.instance.user:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['national_code'].initial = user.national_code
            self.fields['phone_number'].initial = user.phone_number
            self.fields['email'].initial = user.email
            self.fields['date_of_birth'].initial = user.date_of_birth # مقداردهی تاریخ تولد
            self.fields['gender'].initial = user.gender # مقداردهی جنسیت

            # فیلدهای national_code و phone_number برای ویرایش قفل شوند
            self.fields['national_code'].widget.attrs['readonly'] = True
            self.fields['phone_number'].widget.attrs['readonly'] = True

    @transaction.atomic
    def save(self, commit=True):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        national_code = self.cleaned_data.get('national_code')
        phone_number = self.cleaned_data.get('phone_number')
        email = self.cleaned_data.get('email')
        date_of_birth = self.cleaned_data.get('date_of_birth') # دریافت تاریخ تولد
        gender = self.cleaned_data.get('gender') # دریافت جنسیت

        if self.instance and self.instance.pk and self.instance.user:
            # اگر بیمار و کاربر مرتبط وجود دارند، کاربر را به‌روزرسانی کن
            user = self.instance.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.date_of_birth = date_of_birth # به‌روزرسانی تاریخ تولد
            user.gender = gender # به‌روزرسانی جنسیت
            user.save()
        else:
            # اگر بیمار جدید است، کاربر موجود را پیدا کن یا یک کاربر جدید بساز
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
                    user.date_of_birth = date_of_birth # به‌روزرسانی تاریخ تولد
                    user.gender = gender # به‌روزرسانی جنسیت
                    user.save()
            else:
                user = User.objects.create_user(
                    username=phone_number, # یا national_code، مطمئن شوید یونیک است
                    phone_number=phone_number,
                    national_code=national_code,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    date_of_birth=date_of_birth, # پاس دادن تاریخ تولد به create_user
                    gender=gender, # پاس دادن جنسیت به create_user
                    password=None # فرض می‌کنیم create_user پسورد را مدیریت می‌کند
                )
            self.instance.user = user # کاربر را به نمونه بیمار تخصیص بده

        # ذخیره کردن نمونه Patient (که اکنون فیلد user آن تنظیم شده است)
        return super().save(commit=commit)