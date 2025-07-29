from apps.clinic_messenger.models import OTPCode
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User, Role, AccessPermission


# ----------------------------
# فرم نقش‌ها
# ----------------------------
class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name", "code", "description", "permissions"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "permissions": forms.CheckboxSelectMultiple(),
        }
        labels = {
            "name": "نام نقش",
            "code": "کد نقش",
            "description": "توضیحات",
            "permissions": "دسترسی‌ها",
        }


# ----------------------------
# فرم دسترسی‌ها (Permission)
# ----------------------------
class AccessPermissionForm(forms.ModelForm):
    class Meta:
        model = AccessPermission
        fields = ["name", "code", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "name": "نام نمایشی",
            "code": "کد دسترسی",
            "description": "توضیحات",
        }


# ----------------------------
# فرم ساخت یوزر توسط ادمین
# ----------------------------
class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "nickname",
            "national_code",
            "phone_number",
            "email",
            "profile_image",
            "role",
            "is_verified",
        ]
        widgets = {
            "role": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "username": "نام کاربری",
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "nickname": "نام مستعار",
            "national_code": "کد ملی",
            "phone_number": "شماره موبایل",
            "email": "ایمیل",
            "profile_image": "تصویر پروفایل",
            "role": "نقش",
            "is_verified": "تأیید شده توسط ادمین",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


# ----------------------------
# فرم ویرایش یوزر توسط ادمین
# ----------------------------
class UserUpdateForm(UserChangeForm):
    password = None  # حذف فیلد رمز از فرم

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "nickname",
            "national_code",
            "phone_number",
            "email",
            "profile_image",
            "role",
            "is_verified",
            "is_active",
            "phone_verified",
            "email_verified",
        ]
        widgets = {
            "role": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "username": "نام کاربری",
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "nickname": "نام مستعار",
            "national_code": "کد ملی",
            "phone_number": "شماره موبایل",
            "email": "ایمیل",
            "profile_image": "تصویر پروفایل",
            "role": "نقش",
            "is_verified": "تأیید شده",
            "is_active": "فعال",
            "phone_verified": "موبایل تأیید شده",
            "email_verified": "ایمیل تأیید شده",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class OTPRequestForm(forms.Form):
    phone_number = forms.CharField(max_length=15)
    purpose = forms.ChoiceField(choices=OTPCode.PURPOSE_CHOICES)


class OTPVerifyForm(forms.Form):
    phone_number = forms.CharField(max_length=15)
    code = forms.CharField(max_length=6)
    purpose = forms.ChoiceField(choices=OTPCode.PURPOSE_CHOICES)
