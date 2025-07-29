from django import forms
from django.forms import inlineformset_factory

from .models import (
    SMSMessage,
    EmailMessage,
    SMSConfig,
    SMSPattern,
    SMSPatternType,
    SMSPatternVariable
)


class SMSConfigForm(forms.ModelForm):
    class Meta:
        model = SMSConfig
        fields = ["provider", "api_key", "originator", "is_active"]
        widgets = {
            "provider": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثلاً IPPanel"}),
            "api_key": forms.TextInput(attrs={"class": "form-control", "placeholder": "کلید API"}),
            "originator": forms.TextInput(attrs={"class": "form-control", "placeholder": "شماره فرستنده"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SMSMessageForm(forms.ModelForm):
    class Meta:
        model = SMSMessage
        fields = ["to", "body"]
        widgets = {
            "to": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثلاً 09123456789"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "متن پیامک"}),
        }


class SMSPatternForm(forms.ModelForm):
    """
    فرم برای ایجاد و ویرایش پترن‌های پیامک.
    """

    class Meta:
        model = SMSPattern
        fields = ['code', 'name', 'provider', 'body_template', 'config', 'type', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={"class": "form-control"}),
            'name': forms.TextInput(attrs={"class": "form-control"}),
            'provider': forms.TextInput(attrs={"class": "form-control"}),
            'body_template': forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            'config': forms.Select(attrs={"class": "form-select"}),
            'type': forms.Select(attrs={"class": "form-select"}),
            'is_active': forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SMSPatternTypeForm(forms.ModelForm):
    """
    فرم برای ایجاد و ویرایش انواع پترن‌های پیامک.
    """

    class Meta:
        model = SMSPatternType
        fields = ['code', 'title', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={"class": "form-control"}),
            'title': forms.TextInput(attrs={"class": "form-control"}),
            'description': forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            'is_active': forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SMSPatternVariableForm(forms.ModelForm):
    """
    فرم برای ایجاد متغیرهای پترن پیامک.
    """

    class Meta:
        model = SMSPatternVariable
        fields = ['key', 'label', 'data_type', 'required', 'hint']
        widgets = {
            'key': forms.TextInput(attrs={"class": "form-control", "placeholder": "مثلاً full_name"}),
            'label': forms.TextInput(attrs={"class": "form-control", "placeholder": "مثلاً نام کامل"}),
            'data_type': forms.Select(attrs={"class": "form-select"}),
            'required': forms.CheckboxInput(attrs={"class": "form-check-input"}),
            'hint': forms.TextInput(attrs={"class": "form-control", "placeholder": "توضیح بیشتر (اختیاری)"}),
        }


# فرم ست برای اضافه کردن متغیرها به پترن
SMSPatternVariableFormSet = inlineformset_factory(
    parent_model=SMSPattern,
    model=SMSPatternVariable,
    form=SMSPatternVariableForm,
    extra=1,
    can_delete=True
)


class EmailMessageForm(forms.ModelForm):
    class Meta:
        model = EmailMessage
        fields = ["to_email", "subject", "body"]
        widgets = {
            "to_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@email.com"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "موضوع ایمیل"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "متن ایمیل"}),
        }
