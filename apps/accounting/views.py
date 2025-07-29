# apps/accounting/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import (
    BankReceiptForm,
    DocumentAttachmentForm,
    InvoiceForm,
    TransactionForm,
)
from .mixins import ExportMixin
from .models import (
    Account,
    BankReceipt,
    DocumentAttachment,
    Invoice,
    LedgerEntry,
    Transaction,
)


# ----------------- Account -----------------
class AccountListView(LoginRequiredMixin, PermissionRequiredMixin, ExportMixin, ListView):
    model = Account
    template_name = "accounting/account_list.html"
    context_object_name = "accounts"
    paginate_by = 20
    permission_required = "accounting.view_account"


class AccountDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Account
    template_name = "accounting/account_detail.html"
    context_object_name = "account"
    permission_required = "accounting.view_account"


# ----------------- Invoice -----------------
class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ExportMixin, ListView):
    model = Invoice
    template_name = "accounting/invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 20
    permission_required = "accounting.view_invoice"


class InvoiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Invoice
    template_name = "accounting/invoice_detail.html"
    context_object_name = "invoice"
    permission_required = "accounting.view_invoice"


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "accounting/invoice_form.html"
    permission_required = "accounting.add_invoice"
    success_url = reverse_lazy("accounting:invoice_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class InvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "accounting/invoice_form.html"
    permission_required = "accounting.change_invoice"

    def get_success_url(self):
        return self.object.get_absolute_url()


# ----------------- Transaction -----------------
class TransactionListView(LoginRequiredMixin, PermissionRequiredMixin, ExportMixin, ListView):
    model = Transaction
    template_name = "accounting/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20
    permission_required = "accounting.view_transaction"


class TransactionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Transaction
    template_name = "accounting/transaction_detail.html"
    context_object_name = "transaction"
    permission_required = "accounting.view_transaction"


class TransactionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "accounting/transaction_form.html"
    permission_required = "accounting.add_transaction"
    success_url = reverse_lazy("accounting:transaction_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "accounting/transaction_form.html"
    permission_required = "accounting.change_transaction"

    def get_success_url(self):
        return self.object.get_absolute_url()


# ----------------- BankReceipt -----------------
class BankReceiptCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BankReceipt
    form_class = BankReceiptForm
    template_name = "accounting/bankreceipt_form.html"
    permission_required = "accounting.add_bankreceipt"

    def form_valid(self, form):
        transaction_id = self.kwargs["transaction_id"]
        form.instance.transaction = get_object_or_404(Transaction, pk=transaction_id)
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.transaction.get_absolute_url()


class BankReceiptDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = BankReceipt
    template_name = "accounting/bankreceipt_detail.html"
    context_object_name = "bankreceipt"
    permission_required = "accounting.view_bankreceipt"


# ----------------- LedgerEntry -----------------
class LedgerEntryListView(LoginRequiredMixin, PermissionRequiredMixin, ExportMixin, ListView):
    model = LedgerEntry
    template_name = 'accounting/ledgerentry_list.html'
    context_object_name = 'ledger_entries'
    paginate_by = 20
    permission_required = "accounting.view_ledgerentry"


class LedgerEntryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = LedgerEntry
    template_name = 'accounting/ledgerentry_detail.html'
    context_object_name = 'ledger_entry'
    permission_required = "accounting.view_ledgerentry"


# ----------------- DocumentAttachment (رویکرد جدید و اصلاح شده) -----------------
class InvoiceDocumentUploadView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View برای آپلود پیوست برای یک فاکتور مشخص.
    """
    model = DocumentAttachment
    form_class = DocumentAttachmentForm
    template_name = 'accounting/document_form.html'
    permission_required = "accounting.add_documentattachment"

    def dispatch(self, request, *args, **kwargs):
        """ذخیره کردن فاکتور والد برای استفاده در متدهای دیگر."""
        self.invoice = get_object_or_404(Invoice, pk=self.kwargs['invoice_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """اضافه کردن فاکتور به کانتکست تمپلیت."""
        context = super().get_context_data(**kwargs)
        context['invoice'] = self.invoice
        return context

    def form_valid(self, form):
        """اتصال پیوست به فاکتور و کاربر."""
        form.instance.invoice = self.invoice
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """بازگشت به صفحه جزئیات فاکتور والد."""
        return self.invoice.get_absolute_url()


class TransactionDocumentUploadView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View برای آپلود پیوست برای یک تراکنش مشخص.
    """
    model = DocumentAttachment
    form_class = DocumentAttachmentForm
    template_name = 'accounting/document_form.html'
    permission_required = "accounting.add_documentattachment"

    def dispatch(self, request, *args, **kwargs):
        """ذخیره کردن تراکنش والد برای استفاده در متدهای دیگر."""
        self.transaction = get_object_or_404(Transaction, pk=self.kwargs['transaction_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """اضافه کردن تراکنش به کانتکست تمپلیت."""
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.transaction
        return context

    def form_valid(self, form):
        """اتصال پیوست به تراکنش و کاربر."""
        form.instance.transaction = self.transaction
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """بازگشت به صفحه جزئیات تراکنش والد."""
        return self.transaction.get_absolute_url()


# ----------------- DocumentAttachment (View های عمومی) -----------------
class DocumentAttachmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    View برای نمایش لیست تمام پیوست‌ها.
    """
    model = DocumentAttachment
    template_name = 'accounting/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    permission_required = "accounting.view_documentattachment"


class DocumentAttachmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    View برای آپلود یک پیوست عمومی (کاربر باید والد را انتخاب کند).
    """
    model = DocumentAttachment
    form_class = DocumentAttachmentForm
    template_name = 'accounting/document_form.html'
    permission_required = "accounting.add_documentattachment"
    success_url = reverse_lazy('accounting:document_list')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)
