#
# فایل: apps/accounting/models.py
#

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


# 📌 نکته: مدل FinancialDocument به طور کامل حذف شده است.

# مدل‌های Account و LedgerEntry بدون تغییر باقی می‌مانند...
class Account(models.Model):
    # ... (کد این مدل بدون تغییر است)
    code = models.CharField(max_length=20, unique=True, verbose_name="کد حساب")
    name = models.CharField(max_length=100, verbose_name="نام حساب")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    # ⚠️ اصلاح پیشنهادی: استفاده از BigIntegerField برای ریال
    balance = models.BigIntegerField(default=0, verbose_name="مانده حساب (ریال)")

    def __str__(self):
        return f"{self.code} - {self.name}"


class LedgerEntry(models.Model):
    # ... (کد این مدل بدون تغییر است)
    transaction = models.ForeignKey("Transaction", on_delete=models.CASCADE, related_name="ledger_entries")
    account = models.ForeignKey("Account", on_delete=models.PROTECT, verbose_name="حساب")
    debit = models.BigIntegerField(default=0, verbose_name="بدهکار (ریال)")
    credit = models.BigIntegerField(default=0, verbose_name="بستانکار (ریال)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "ثبت دفتر کل"
        verbose_name_plural = "ثبت‌های دفتر کل"
        ordering = ["-created_at"]

    def __str__(self):
        return f"دفترکل: {self.account} | بدهکار: {self.debit:,} | بستانکار: {self.credit:,}"


#
# ✅ مدل فاکتور (Invoice) - ساختار جدید و بهینه شده
#
class Invoice(models.Model):
    """
    ✅ فاکتور - صورت‌حساب (پرداخت یا خرید).
    این مدل جایگزین FinancialDocument شده و تمام مسئولیت‌های آن را به عهده دارد.
    """
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('open', 'باز'),
        ('paid', 'پرداخت شده'),
        ('void', 'باطل شده'),
        ('uncollectible', 'غیرقابل وصول'),
    ]

    invoice_number = models.CharField(max_length=30, unique=True, verbose_name="شماره فاکتور")

    # ارتباطات
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="کاربر مربوطه (بیمار/مشتری)"
    )
    # 📌 ارجاع رشته‌ای برای جلوگیری از Circular Import
    related_reception = models.OneToOneField(
        "reception.Reception", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="invoice", verbose_name="پذیرش مرتبط"
    )
    related_appointment = models.ForeignKey(
        "appointments.Appointment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", verbose_name="نوبت مرتبط"
    )

    # فیلدهای مالی (ادغام شده از FinancialDocument)
    discount = models.BigIntegerField(default=0, verbose_name="تخفیف (ریال)")
    # ⚠️ اصلاح پیشنهادی: استفاده از BigIntegerField برای محاسبات دقیق پولی
    tax = models.BigIntegerField(default=0, verbose_name="مالیات (ریال)")

    # وضعیت و تاریخ‌ها
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="وضعیت")
    issue_date = models.DateField(default=timezone.now, verbose_name="تاریخ صدور")
    due_date = models.DateField(blank=True, null=True, verbose_name="تاریخ سررسید")

    # فیلدهای مدیریتی
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_invoices", verbose_name="کاربر ایجادکننده"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        ordering = ['-issue_date', '-created_at']
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['related_user']),
            models.Index(fields=['issue_date']),
        ]

    def __str__(self):
        return f"فاکتور {self.invoice_number} - وضعیت: {self.get_status_display()}"

    def generate_invoice_number(self):
        """متد تولید شماره فاکتور: فرمت: INV-YYMMDD-xxxx"""
        today_str = timezone.now().strftime('%y%m%d')
        count = Invoice.objects.filter(created_at__date=timezone.now().date()).count() + 1
        return f"INV-{today_str}-{count:04d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

    @property
    def total_items_amount(self):
        """جمع مبلغ آیتم‌ها قبل از تخفیف و مالیات."""
        return self.items.aggregate(total=models.Sum('total_price'))['total'] or 0

    @property
    def final_amount(self):
        """مبلغ نهایی قابل پرداخت (پس از اعمال تخفیف و مالیات)."""
        return (self.total_items_amount - self.discount) + self.tax

    @property
    def paid_amount(self):
        """جمع مبالغ پرداخت شده برای این فاکتور."""
        # ⚠️ اصلاح پیشنهادی: استفاده از BigIntegerField
        return self.transactions.filter(transaction_type='inflow').aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def debt(self):
        """بدهی باقی‌مانده."""
        return max(self.final_amount - self.paid_amount, 0)

    @property
    def is_paid(self):
        """آیا فاکتور به طور کامل پرداخت شده است؟"""
        return self.debt <= 0

    def get_absolute_url(self):
        return reverse('accounting:invoice_detail', kwargs={'pk': self.pk})


#
# ✅ مدل آیتم فاکتور (InvoiceItem) - ساختار جدید و بهینه شده
#
class InvoiceItem(models.Model):
    """
    آیتم‌های یک فاکتور. هر آیتم می‌تواند یک خدمت یا یک کالا باشد.
    """
    # 📌 اصلاح: حذف فیلد financial_document و اتصال مستقیم به Invoice
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name="items", verbose_name="فاکتور"
    )

    # 📌 ارجاع رشته‌ای برای جلوگیری از Circular Import
    service_tariff = models.ForeignKey(
        "reception.ServiceTariff", null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name="تعرفه خدمت"
    )
    # 📌 ارجاع رشته‌ای برای جلوگیری از Circular Import
    product = models.ForeignKey(
        "inventory.Item", null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name="کالا/محصول"
    )
    description = models.CharField(max_length=255, verbose_name="شرح آیتم")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name="تعداد/مقدار")
    # ⚠️ اصلاح پیشنهادی: استفاده از BigIntegerField
    unit_price = models.BigIntegerField(verbose_name="قیمت واحد (ریال)")
    total_price = models.BigIntegerField(editable=False, verbose_name="جمع کل (ریال)")

    class Meta:
        verbose_name = "آیتم فاکتور"
        verbose_name_plural = "آیتم‌های فاکتور"

    def clean(self):
        if (self.service_tariff and self.product) or (not self.service_tariff and not self.product):
            raise ValidationError("باید دقیقاً یکی از 'تعرفه خدمت' یا 'کالا/محصول' را وارد کنید.")

    def save(self, *args, **kwargs):
        # اگر کاربر شرح را وارد نکرده بود، آن را به صورت خودکار پر کن
        if not self.description:
            if self.service_tariff:
                self.description = self.service_tariff.service_type.name
            elif self.product:
                self.description = self.product.name
        # محاسبه قیمت کل
        self.total_price = int(self.quantity * self.unit_price)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} (تعداد: {self.quantity})"


#
# ✅ مدل تراکنش (Transaction) - با اصلاح پیشنهادی واحد پولی
#
class Transaction(models.Model):
    # ... (کد این مدل با اصلاح amount)
    # ⚠️ اصلاح پیشنهادی: استفاده از BigIntegerField برای ریال
    amount = models.BigIntegerField(verbose_name="مبلغ (ریال)")
    # ... (بقیه فیلدها بدون تغییر باقی می‌مانند)
    TRANSACTION_TYPE_CHOICES = [
        ('inflow', 'ورودی'),
        ('outflow', 'خروجی'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقدی'),
        ('card', 'کارت‌خوان'),
        ('online', 'پرداخت آنلاین'),
        ('insurance', 'بیمه'),
        ('combined', 'ترکیبی'),
        ('other', 'سایر'),
    ]

    related_reception = models.ForeignKey(
        "reception.Reception", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="transactions",
        verbose_name="پذیرش مرتبط (اختیاری)"
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name="transactions", verbose_name="فاکتور"
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name="نوع تراکنش")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="روش پرداخت")
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="user_transactions", verbose_name="کاربر"
    )
    # ... (بقیه فیلدها)
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_transactions", verbose_name="ثبت‌کننده"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        indexes = [
            models.Index(fields=['transaction_type', 'payment_method']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount:,} ریال"

    def save(self, *args, **kwargs):
        # این متد می‌تواند منطق ایجاد خودکار LedgerEntry را در خود داشته باشد
        super().save(*args, **kwargs)
        # و همچنین وضعیت فاکتور مرتبط را به‌روز کند
        if self.invoice:
            if self.invoice.is_paid:
                self.invoice.status = 'paid'
            else:
                self.invoice.status = 'open'
            self.invoice.save()

    def get_absolute_url(self):
        return reverse('accounting:transaction_detail', kwargs={'pk': self.pk})


class BankReceipt(models.Model):
    """
    ✅ رسید بانکی (اختیاری) برای هر تراکنش.
    """
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE,
                                       related_name="bank_receipt", verbose_name="تراکنش")
    file = models.FileField(upload_to='transactions/bank_receipts/', verbose_name="فایل رسید")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="uploaded_receipts", verbose_name="آپلودکننده"
    )
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ آپلود")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    def __str__(self):
        return f"رسید بانکی برای {self.transaction}"


class DocumentAttachment(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name="documents", blank=True, null=True, verbose_name="فاکتور"
    )
    transaction = models.ForeignKey(
        "Transaction", on_delete=models.CASCADE,
        related_name="documents", blank=True, null=True, verbose_name="تراکنش"
    )
    file = models.FileField(upload_to="accounting/documents/", verbose_name="فایل")
    doc_type = models.CharField(max_length=50, verbose_name="نوع فایل (مثلاً: رسید، قرارداد، …)")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    verbose_name="آپلودکننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()
