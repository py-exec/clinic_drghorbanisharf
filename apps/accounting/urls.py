# apps/accounting/urls.py

from django.urls import path

from . import views

app_name = 'accounting'

urlpatterns = [
    # ------------------ فاکتورها (Invoices) ------------------
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    # مسیر جدید برای آپلود پیوست به یک فاکتور مشخص
    path('invoices/<int:invoice_pk>/documents/upload/', views.InvoiceDocumentUploadView.as_view(),
         name='invoice_document_upload'),

    # ------------------ تراکنش‌ها (Transactions) ------------------
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    # مسیر جدید برای آپلود پیوست به یک تراکنش مشخص
    path('transactions/<int:transaction_pk>/documents/upload/', views.TransactionDocumentUploadView.as_view(),
         name='transaction_document_upload'),

    # ------------------ حساب‌ها (Accounts) ------------------
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),

    # ------------------ سایر URLهای پشتیبانی ------------------
    # رسیدهای بانکی (Bank Receipts)
    path('transactions/<int:transaction_id>/bank-receipt/create/', views.BankReceiptCreateView.as_view(),
         name='bankreceipt_create'),
    path('bank-receipts/<int:pk>/', views.BankReceiptDetailView.as_view(), name='bankreceipt_detail'),

    # ورودی‌های دفتر کل (Ledger Entries)
    path('ledger-entries/', views.LedgerEntryListView.as_view(), name='ledgerentry_list'),
    path('ledger-entries/<int:pk>/', views.LedgerEntryDetailView.as_view(), name='ledgerentry_detail'),

    # پیوست‌های اسناد (Document Attachments)
    path('documents/', views.DocumentAttachmentListView.as_view(), name='document_list'),
    path('documents/upload/', views.DocumentAttachmentCreateView.as_view(), name='document_create'),
]
