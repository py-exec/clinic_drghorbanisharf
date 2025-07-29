# apps/accounting/forms.py

from django import forms

from .models import (
    BankReceipt,
    DocumentAttachment,
    Invoice,
    Transaction
)


class InvoiceForm(forms.ModelForm):
    """
    فرم کامل برای ایجاد و ویرایش فاکتور.
    فیلدهای invoice_number و created_by به صورت خودکار در View مدیریت می‌شوند.
    """

    class Meta:
        model = Invoice
        fields = [
            'related_user',
            'related_reception',
            'related_appointment',
            'issue_date',
            'due_date',
            'status',
            'discount',
            'tax',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'یادداشت‌های داخلی یا توضیحات برای مشتری...'}),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TransactionForm(forms.ModelForm):
    """
    فرم کامل برای ایجاد و ویرایش تراکنش.
    فیلد created_by به صورت خودکار در View مدیریت می‌شود.
    """

    class Meta:
        model = Transaction
        fields = [
            'invoice',
            'amount',
            'transaction_type',
            'payment_method',
            'related_user',
            'description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'شرح تراکنش...'}),
        }


class BankReceiptForm(forms.ModelForm):
    """
    فرم برای آپلود رسید بانکی.
    فیلدهای transaction و uploaded_by به صورت خودکار در View مدیریت می‌شوند.
    """

    class Meta:
        model = BankReceipt
        fields = ['file', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'یادداشت‌های مربوط به رسید...'}),
        }


class DocumentAttachmentForm(forms.ModelForm):
    """
    فرم هوشمند برای آپلود پیوست.
    این فرم می‌تواند هم برای آپلود عمومی و هم برای آپلود در زمینه یک فاکتور یا تراکنش خاص استفاده شود.
    """

    class Meta:
        model = DocumentAttachment
        fields = [
            'invoice',
            'transaction',
            'file',
            'doc_type',
        ]
        widgets = {
            'doc_type': forms.TextInput(attrs={'placeholder': 'مثلاً: رسید، قرارداد، ...'}),
        }

    def __init__(self, *args, **kwargs):
        # این آرگومان‌های سفارشی از View ارسال می‌شوند تا فرم هوشمند عمل کند.
        invoice_instance = kwargs.pop('invoice', None)
        transaction_instance = kwargs.pop('transaction', None)

        super().__init__(*args, **kwargs)

        # اگر فرم در صفحه جزئیات یک فاکتور مشخص استفاده شود،
        # فیلد انتخاب فاکتور و تراکنش را مخفی می‌کنیم چون والد مشخص است.
        if invoice_instance:
            self.fields['invoice'].widget = forms.HiddenInput()
            self.fields['invoice'].initial = invoice_instance
            self.fields.pop('transaction')

        # اگر فرم در صفحه جزئیات یک تراکنش مشخص استفاده شود،
        # فیلد انتخاب فاکتور و تراکنش را مخفی می‌کنیم.
        elif transaction_instance:
            self.fields['transaction'].widget = forms.HiddenInput()
            self.fields['transaction'].initial = transaction_instance
            self.fields.pop('invoice')

    def clean(self):
        """
        اعتبارسنجی برای اطمینان از اینکه پیوست فقط به یک والد متصل است.
        """
        cleaned_data = super().clean()
        invoice = cleaned_data.get("invoice")
        transaction = cleaned_data.get("transaction")

        # این شرط برای فرم عمومی (نه فرم‌های داخل صفحه جزئیات) اعمال می‌شود.
        if self.fields.get('invoice') and self.fields.get('transaction'):
            if invoice and transaction:
                raise forms.ValidationError("یک پیوست نمی‌تواند همزمان به فاکتور و تراکنش متصل باشد.")
            if not invoice and not transaction:
                raise forms.ValidationError("یک پیوست باید حداقل به یک فاکتور یا تراکنش متصل باشد.")

        return cleaned_data
