from django import forms
from django.forms import inlineformset_factory
from .models import (
    Item, StockIn, StockInItem, StockOut, StockOutItem
)
from .models import (
    Loan, MaintenanceLog, ScheduledMaintenance
)
from .models import (
    CalibrationLog, DecommissionLog, PatientUsageLog,
    ItemMovementLog, DocumentAttachment, TaskQueue
)

# ---------------------------------------
# فرم تعریف کالا (Item)
# ---------------------------------------

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کالا'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثلاً عدد، لیتر، بسته'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'warranty_provider': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_consumable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_loanable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_decommissioned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'انتخاب دسته‌بندی'
        self.fields['status'].empty_label = 'انتخاب وضعیت'
        self.fields['supplier'].empty_label = 'انتخاب تأمین‌کننده'
        self.fields['warranty_provider'].empty_label = 'انتخاب گارانتی‌دهنده'

    def clean_serial_number(self):
        serial = self.cleaned_data.get('serial_number')
        if serial and Item.objects.exclude(pk=self.instance.pk).filter(serial_number=serial).exists():
            raise forms.ValidationError("این شماره سریال قبلاً ثبت شده است.")
        return serial

    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if barcode and Item.objects.exclude(pk=self.instance.pk).filter(barcode=barcode).exists():
            raise forms.ValidationError("این بارکد قبلاً ثبت شده است.")
        return barcode


# ---------------------------------------
# فرم سند ورود کالا به انبار (StockIn)
# ---------------------------------------

class StockInForm(forms.ModelForm):
    class Meta:
        model = StockIn
        fields = ['supplier', 'invoice_number', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StockInItemForm(forms.ModelForm):
    class Meta:
        model = StockInItem
        fields = ['item', 'quantity', 'unit_price', 'batch_number', 'expiration_date']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

StockInItemFormSet = inlineformset_factory(
    StockIn,
    StockInItem,
    form=StockInItemForm,
    extra=1,
    can_delete=True
)

# ---------------------------------------
# فرم سند خروج کالا از انبار (StockOut)
# ---------------------------------------

class StockOutForm(forms.ModelForm):
    class Meta:
        model = StockOut
        fields = ['department', 'staff', 'purpose', 'notes']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'staffs': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StockOutItemForm(forms.ModelForm):
    class Meta:
        model = StockOutItem
        fields = ['item', 'quantity']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

StockOutItemFormSet = inlineformset_factory(
    StockOut,
    StockOutItem,
    form=StockOutItemForm,
    extra=1,
    can_delete=True
)



# ---------------------------------------
# فرم امانت تجهیز به بیمار (Loan)
# ---------------------------------------

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام بیمار'}),
            'external_patient_id': forms.TextInput(attrs={'class': 'form-control'}),
            'loan_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'staffs': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].empty_label = 'انتخاب وضعیت'


# ---------------------------------------
# فرم ثبت تعمیرات تجهیز (MaintenanceLog)
# ---------------------------------------

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'date_reported': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'issue_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'maintenance_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'technician': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].empty_label = 'انتخاب وضعیت'


# ---------------------------------------
# فرم نگهداری برنامه‌ریزی‌شده (ScheduledMaintenance)
# ---------------------------------------

class ScheduledMaintenanceForm(forms.ModelForm):
    class Meta:
        model = ScheduledMaintenance
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'interval_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].empty_label = 'انتخاب وضعیت'


# ---------------------------------------
# فرم ثبت کالیبراسیون (CalibrationLog)
# ---------------------------------------

class CalibrationLogForm(forms.ModelForm):
    class Meta:
        model = CalibrationLog
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'calibration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'performed_by': forms.Select(attrs={'class': 'form-control'}),
            'calibration_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ---------------------------------------
# فرم ثبت اسقاط تجهیز (DecommissionLog)
# ---------------------------------------

class DecommissionForm(forms.ModelForm):
    class Meta:
        model = DecommissionLog
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'confirmed_by': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# ---------------------------------------
# فرم ثبت استفاده مستقیم توسط بیمار (PatientUsageLog)
# ---------------------------------------

class PatientUsageLogForm(forms.ModelForm):
    class Meta:
        model = PatientUsageLog
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.TextInput(attrs={'class': 'form-control'}),
            'external_patient_id': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'performed_by': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# ---------------------------------------
# فرم ثبت جابجایی تجهیز (ItemMovementLog)
# ---------------------------------------

class ItemMovementForm(forms.ModelForm):
    class Meta:
        model = ItemMovementLog
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'from_location': forms.TextInput(attrs={'class': 'form-control'}),
            'to_location': forms.TextInput(attrs={'class': 'form-control'}),
            'moved_by': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# ---------------------------------------
# فرم آپلود فایل ضمیمه (DocumentAttachment)
# ---------------------------------------

class DocumentAttachmentForm(forms.ModelForm):
    class Meta:
        model = DocumentAttachment
        exclude = []
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'doc_type': forms.Select(attrs={'class': 'form-control'}),
            'uploaded_by': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doc_type'].empty_label = 'انتخاب نوع فایل'


# ---------------------------------------
# فرم ثبت وظایف و هشدارها (TaskQueue)
# ---------------------------------------

class TaskQueueForm(forms.ModelForm):
    class Meta:
        model = TaskQueue
        exclude = []
        widgets = {
            'task_type': forms.Select(attrs={'class': 'form-control'}),
            'related_item': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'auto_generated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['task_type'].empty_label = 'انتخاب نوع وظیفه'
        self.fields['status'].empty_label = 'انتخاب وضعیت'
