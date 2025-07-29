# apps/reception/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory
from django.utils import timezone

from apps.patient.models import Patient
from .models import Reception, ServiceTariff, ServiceType, ReceptionService


class ReceptionForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=ServiceTariff.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="خدمات انتخابی",
    )

    cash_amount = forms.IntegerField(
        required=False,
        min_value=0,
        label="پرداخت نقدی",
        widget=forms.NumberInput(attrs={
            'class': 'form-control amount-input',
            'placeholder': 'مثلاً ۵۰۰۰۰۰'
        })
    )

    card_amount = forms.IntegerField(
        required=False,
        min_value=0,
        label="پرداخت با کارت‌خوان",
        widget=forms.NumberInput(attrs={
            'class': 'form-control amount-input',
            'placeholder': 'مثلاً ۳۰۰۰۰۰'
        })
    )

    class Meta:
        model = Reception
        exclude = [
            'patient',
            'created_by',
            'updated_at',
            'total_cost',
            'admission_date',
            'admission_code',
        ]
        widgets = {
            'service_level': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'services': 'خدمات انتخابی',
            'cash_amount': 'پرداخت نقدی',
            'card_amount': 'پرداخت با کارت‌خوان',
            'notes': 'یادداشت',
            'discount': 'تخفیف',
            'status': 'وضعیت',
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop("patient", None)
        super().__init__(*args, **kwargs)

        today = timezone.now().date()
        self.fields['services'].queryset = ServiceTariff.objects.filter(
            is_active=True
        ).filter(
            Q(valid_from__isnull=True) | Q(valid_from__lte=today)
        ).filter(
            Q(valid_to__isnull=True) | Q(valid_to__gte=today)
        ).select_related('service_type').order_by('service_type__name')

        print(f"🧊 [FORM INIT] queryset count: {self.fields['services'].queryset.count()}", flush=True)

    def get_context_data(self, form=None):
        if form is None:
            form = ReceptionForm()
        print(f"🧃 queryset in form init: {form.fields['services'].queryset}")

        return {
            "form": form,
            "patient": self.patient,
            "service_tariff_map": {
                str(t.id): t.amount for t in form.fields['services'].queryset
            }
        }

    def clean_services(self):
        services = self.cleaned_data.get('services')
        if not services:
            raise ValidationError("حداقل یک خدمت باید انتخاب شود.")
        return services

    def clean(self):
        cleaned_data = super().clean()

        cash = cleaned_data.get('cash_amount') or 0
        card = cleaned_data.get('card_amount') or 0
        total_paid = cash + card
        cleaned_data['total_payment'] = total_paid

        services = cleaned_data.get('services') or []
        total_service_cost = sum([s.amount for s in services])
        cleaned_data['total_service_cost'] = total_service_cost

        if total_paid <= 0:
            raise ValidationError("حداقل یکی از روش‌های پرداخت باید وارد شود.")

        if total_paid > total_service_cost:
            raise ValidationError("مبلغ پرداختی نمی‌تواند بیشتر از مبلغ خدمات باشد.")

        return cleaned_data

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()

                # پاک کردن خدمات قبلی
                self.object.receptionservice_set.all().delete()

                # ساختن خدمات جدید
                for service in form.cleaned_data['services']:
                    ReceptionService.objects.create(
                        reception=self.object,
                        tariff=service,
                        cost=service.amount
                    )

                messages.success(self.request, "پذیرش با موفقیت ویرایش شد.")
                return redirect(self.get_success_url())
        except Exception as e:
            logging.exception("⛔ خطا در ویرایش پذیرش")
            messages.error(self.request, "ویرایش با خطا مواجه شد.")
            return self.form_invalid(form)


class PatientLookupForm(forms.Form):
    national_code = forms.CharField(
        label="کد ملی",
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'کد ملی',
            'class': 'form-control'
        })
    )
    phone_number = forms.CharField(
        label="شماره تماس",
        required=False,
        max_length=11,
        widget=forms.TextInput(attrs={
            'placeholder': 'مثال: 09123456789',
            'class': 'form-control'
        })
    )
    record_number = forms.CharField(
        label="شماره پرونده",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'شماره پرونده',
            'class': 'form-control'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        national_code = cleaned_data.get("national_code")
        phone_number = cleaned_data.get("phone_number")
        record_number = cleaned_data.get("record_number")

        if not (national_code or phone_number or record_number):
            raise forms.ValidationError("حداقل یکی از فیلدها باید وارد شود.")
        return cleaned_data


