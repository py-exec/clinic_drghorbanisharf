from django import forms

from .models import SpecialtyCategory, Specialty, Doctor


# ----------------------------
# فرم دسته تخصص‌ها
# ----------------------------
class SpecialtyCategoryForm(forms.ModelForm):
    class Meta:
        model = SpecialtyCategory
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ----------------------------
# فرم تخصص
# ----------------------------
class SpecialtyForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ["title", "category", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ----------------------------
# فرم پزشک
# ----------------------------
class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ["slug", "created_at"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "specialty": forms.Select(attrs={"class": "form-select"}),
            "medical_code": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "education": forms.TextInput(attrs={"class": "form-control"}),
            "university": forms.TextInput(attrs={"class": "form-control"}),
            "work_experience": forms.NumberInput(attrs={"class": "form-control"}),
            "clinic_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "clinic_phone": forms.TextInput(attrs={"class": "form-control"}),
            "clinic_location": forms.TextInput(attrs={"class": "form-control"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "tags": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
