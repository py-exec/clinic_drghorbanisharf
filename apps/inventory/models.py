from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

#۱ شرکت‌ها، نمایندگی‌ها و طرف‌های قرارداد
class Partner(models.Model):
    SUPPLIER = 'supplier'
    WARRANTY = 'warranty'
    MAINTENANCE = 'maintenance'
    CALIBRATION = 'calibration'

    PARTNER_TYPES = [
        (SUPPLIER, 'تأمین‌کننده'),
        (WARRANTY, 'گارانتی‌دهنده'),
        (MAINTENANCE, 'شرکت نگهداری'),
        (CALIBRATION, 'مرکز کالیبراسیون'),
    ]

    name = models.CharField(max_length=255, verbose_name="نام شرکت")
    type = models.CharField(max_length=20, choices=PARTNER_TYPES, verbose_name="نوع")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="شخص تماس")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

#۲ اطلاعات پایه هر تجهیز یا کالای انبار
class Item(models.Model):
    CATEGORY_CHOICES = [
        ('drug', 'دارو'),
        ('consumable', 'مصرفی'),
        ('equipment', 'تجهیزات پزشکی'),
        ('capital', 'سرمایه‌ای'),
        ('loanable', 'قابل امانت'),
    ]

    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('in_use', 'در حال استفاده'),
        ('in_repair', 'در حال تعمیر'),
        ('damaged', 'خراب‌شده'),
        ('lost', 'مفقودی'),
        ('decommissioned', 'از رده خارج'),
        ('with_patient', 'در اختیار بیمار'),
    ]

    name = models.CharField(max_length=255, verbose_name="نام کالا")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="دسته‌بندی")
    unit = models.CharField(max_length=50, default='واحد', verbose_name="واحد شمارش")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="برند")
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name="مدل")
    manufacturer = models.CharField(max_length=100, blank=True, null=True, verbose_name="سازنده")
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="شماره سریال")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="بارکد")
    purchase_date = models.DateField(blank=True, null=True, verbose_name="تاریخ خرید")
    warranty_start = models.DateField(blank=True, null=True, verbose_name="شروع گارانتی")
    warranty_expiry = models.DateField(blank=True, null=True, verbose_name="پایان گارانتی")
    warranty_document = models.FileField(upload_to='warranties/', blank=True, null=True, verbose_name="فایل گارانتی")
    warranty_provider = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='warranty_items', verbose_name="شرکت گارانتی‌دهنده")
    supplier = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_items', verbose_name="تأمین‌کننده")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="وضعیت فعلی")
    is_consumable = models.BooleanField(default=False, verbose_name="مصرفی است؟")
    is_loanable = models.BooleanField(default=False, verbose_name="امکان امانت دارد؟")
    is_decommissioned = models.BooleanField(default=False, verbose_name="از رده خارج شده؟")
    current_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="محل نگهداری فعلی")

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        ordering = ["name"]
        verbose_name = "کالا"
        verbose_name_plural = "کالاها"

    def __str__(self):
        return f"{self.name} ({self.serial_number or 'بدون سریال'})"

#۳ ثبت موجودی کالا در محل مشخص با اطلاعات دقیق
class Inventory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="کالا")
    quantity = models.PositiveIntegerField(default=0, verbose_name="تعداد")
    location = models.CharField(max_length=255, verbose_name="محل نگهداری")
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="شماره بچ / سری ساخت")
    expiration_date = models.DateField(blank=True, null=True, verbose_name="تاریخ انقضا")
    min_required = models.PositiveIntegerField(default=0, verbose_name="حداقل موجودی لازم")

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        unique_together = ('item', 'batch_number', 'location')
        ordering = ['-created_at']
        verbose_name = "موجودی کالا"
        verbose_name_plural = "موجودی‌ها"

    def __str__(self):
        return f"{self.item.name} @ {self.location} ({self.quantity})"

#۴ ثبت سند ورود به انبار (از تأمین‌کننده / فاکتور)
class StockIn(models.Model):
    date = models.DateField(auto_now_add=True, verbose_name="تاریخ ورود")
    supplier = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="تأمین‌کننده")
    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="شماره فاکتور")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['-date']
        verbose_name = "ورود به انبار"
        verbose_name_plural = "ورودهای انبار"

    def __str__(self):
        return f"رسید ورود #{self.id} - {self.date}"

#۵ جزئیات کالاهای هر رسید ورود
class StockInItem(models.Model):
    stock_in = models.ForeignKey(StockIn, on_delete=models.CASCADE, related_name='items', verbose_name="رسید ورود")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="کالا")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="قیمت واحد")
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="شماره بچ")
    expiration_date = models.DateField(blank=True, null=True, verbose_name="تاریخ انقضا")

    def __str__(self):
        return f"{self.quantity} × {self.item.name} در رسید #{self.stock_in.id}"

#۶ سند خروج کالا از انبار (برای مصرف، خرابی، انتقال)
class StockOut(models.Model):
    date = models.DateField(auto_now_add=True, verbose_name="تاریخ خروج")
    department = models.CharField(max_length=100, verbose_name="واحد مقصد")
    staff = models.CharField(max_length=100, verbose_name="تحویل‌گیرنده / مسئول")
    purpose = models.CharField(max_length=255, blank=True, null=True, verbose_name="هدف یا توضیح")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="ایجاد شده در")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        ordering = ['-date']
        verbose_name = "خروج از انبار"
        verbose_name_plural = "خروج‌های انبار"

    def __str__(self):
        return f"خروج #{self.id} - {self.date}"

#۷ جزئیات اقلام خروجی در هر سند خروج از انبار
class StockOutItem(models.Model):
    stock_out = models.ForeignKey(StockOut, on_delete=models.CASCADE, related_name='items', verbose_name="سند خروج")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="کالا")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")

    def __str__(self):
        return f"{self.quantity} × {self.item.name} در خروج #{self.stock_out.id}"

#۸ ثبت امانت تجهیز به بیمار به همراه وضعیت و تاریخ بازگشت
class Loan(models.Model):
    STATUS_CHOICES = [
        ('loaned', 'در امانت'),
        ('returned', 'بازگشته'),
        ('damaged', 'خراب‌شده'),
        ('lost', 'مفقودی'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    patient = models.CharField(max_length=255, verbose_name="نام بیمار")
    external_patient_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="کد بیمار (اختیاری)")
    loan_date = models.DateField(verbose_name="تاریخ امانت")
    expected_return_date = models.DateField(blank=True, null=True, verbose_name="تاریخ بازگشت مورد انتظار")
    return_date = models.DateField(blank=True, null=True, verbose_name="تاریخ بازگشت واقعی")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='loaned', verbose_name="وضعیت")
    staff = models.CharField(max_length=255, verbose_name="مسئول ثبت / تحویل")
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="ثبت‌کننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        ordering = ['-loan_date']
        verbose_name = "امانت تجهیز"
        verbose_name_plural = "امانت‌های تجهیزات"

    def __str__(self):
        return f"{self.item.name} → {self.patient} @ {self.loan_date}"

#۹ ثبت استفاده از تجهیز توسط بیمار بدون امانت
class PatientUsageLog(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    patient = models.CharField(max_length=255, verbose_name="نام بیمار")
    external_patient_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="کد بیمار (اختیاری)")
    date = models.DateField(verbose_name="تاریخ استفاده")
    performed_by = models.CharField(max_length=255, verbose_name="کاربر / پرسنل انجام‌دهنده")
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return f"{self.item.name} → {self.patient} @ {self.date}"

#۱۰ لاگ ثبت تعمیر، وضعیت تعمیر، شرکت مجری و هزینه‌ها
class MaintenanceLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('repaired', 'تعمیر شده'),
        ('replaced', 'تعویض شده'),
        ('irreparable', 'غیرقابل تعمیر'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    date_reported = models.DateField(verbose_name="تاریخ گزارش خرابی")
    maintenance_date = models.DateField(blank=True, null=True, verbose_name="تاریخ انجام تعمیر")
    issue_description = models.TextField(verbose_name="شرح خرابی")
    maintenance_action = models.TextField(blank=True, null=True, verbose_name="اقدام انجام‌شده")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="هزینه (تومان)")
    company = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شرکت تعمیرکار")
    technician = models.CharField(max_length=255, blank=True, null=True, verbose_name="تکنسین")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"تعمیر {self.item.name} - {self.status}"

#۱۱ ثبت گواهی کالیبراسیون تجهیزات با تاریخ انقضا
class CalibrationLog(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    calibration_date = models.DateField(verbose_name="تاریخ کالیبراسیون")
    expiration_date = models.DateField(verbose_name="تاریخ انقضای کالیبراسیون")
    performed_by = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شرکت کالیبراسیون")
    calibration_certificate = models.FileField(upload_to='calibrations/', blank=True, null=True, verbose_name="گواهی کالیبراسیون")
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return f"{self.item.name} - کالیبراسیون {self.calibration_date}"

#۱۲ ثبت علت و زمان از رده خارج شدن تجهیز
class DecommissionLog(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    date = models.DateField(verbose_name="تاریخ اسقاط")
    reason = models.TextField(verbose_name="علت اسقاط")
    confirmed_by = models.CharField(max_length=255, verbose_name="تأییدکننده")
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return f"{self.item.name} - اسقاط در {self.date}"

#۱۳ تاریخچه تغییر وضعیت تجهیز با ثبت کاربر و یادداشت
class ItemStatusHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    status = models.CharField(max_length=20, choices=Item.STATUS_CHOICES, verbose_name="وضعیت جدید")
    change_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تغییر")
    changed_by = models.CharField(max_length=255, verbose_name="کاربر تغییردهنده")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"{self.item.name} → {self.status} @ {self.change_date}"

#۱۴ بارگذاری فایل‌های مرتبط با تجهیز (دفترچه راهنما، گارانتی، گواهی و ...)
class DocumentAttachment(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('manual', 'دفترچه راهنما'),
        ('repair_report', 'گزارش تعمیر'),
        ('calibration_certificate', 'گواهی کالیبراسیون'),
        ('warranty', 'سند گارانتی'),
        ('other', 'سایر'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attachments', verbose_name="تجهیز")
    file = models.FileField(upload_to='attachments/', verbose_name="فایل")
    doc_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, verbose_name="نوع فایل")
    uploaded_by = models.CharField(max_length=255, verbose_name="آپلودکننده")
    upload_date = models.DateField(auto_now_add=True, verbose_name="تاریخ بارگذاری")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"{self.item.name} - {self.get_doc_type_display()}"

#۱۵ ثبت سابقه جابجایی تجهیز بین بخش‌ها یا اتاق‌ها
class ItemMovementLog(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    from_location = models.CharField(max_length=255, verbose_name="از محل")
    to_location = models.CharField(max_length=255, verbose_name="به محل")
    moved_by = models.CharField(max_length=255, verbose_name="کاربر جابجاکننده")
    move_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ جابجایی")
    purpose = models.CharField(max_length=255, blank=True, null=True, verbose_name="هدف جابجایی")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"{self.item.name} moved → {self.to_location} @ {self.move_date}"

#۱۶ برنامه نگهداری پیشگیرانه برای تجهیزات سرمایه‌ای
class ScheduledMaintenance(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="تجهیز")
    interval_days = models.PositiveIntegerField(verbose_name="دوره (روز)")
    next_due_date = models.DateField(verbose_name="تاریخ سررسید بعدی")
    assigned_to = models.CharField(max_length=255, verbose_name="مسئول انجام")
    status = models.CharField(max_length=50, choices=[
        ('pending', 'در انتظار'),
        ('done', 'انجام‌شده'),
        ('overdue', 'به تعویق افتاده'),
    ], default='pending', verbose_name="وضعیت")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"PM برای {self.item.name} → {self.next_due_date}"

#۱۷ صف وظایف سیستم شامل یادآورها، هشدارها و کارهای انسانی
class TaskQueue(models.Model):
    TASK_TYPE_CHOICES = [
        ('return_loan', 'بازگشت امانت از بیمار'),
        ('maintenance', 'نگهداری دوره‌ای'),
        ('calibration', 'کالیبراسیون دوره‌ای'),
        ('low_stock', 'هشدار کمبود موجودی'),
        ('other', 'سایر'),
    ]

    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, verbose_name="نوع وظیفه")
    related_item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True, verbose_name="تجهیز مرتبط")
    assigned_to = models.CharField(max_length=255, verbose_name="واگذار شده به")
    due_date = models.DateField(verbose_name="تاریخ سررسید")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('completed', 'انجام شده'),
        ('overdue', 'به تعویق افتاده'),
    ], default='pending', verbose_name="وضعیت")
    auto_generated = models.BooleanField(default=False, verbose_name="ایجادشده توسط سیستم")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.related_item} - {self.status}"