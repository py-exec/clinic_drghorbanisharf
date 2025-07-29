import re
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords
from apps.accounts.models import Role

# 📌 نکات ایمپورت:
#   - ارجاع به مدل‌ها از اپ‌های دیگر (مانند Patient، Appointment، Transaction، Invoice)
#     به صورت رشته‌ای در ForeignKey/ManyToManyField انجام می‌شود تا از Circular Import جلوگیری شود.
#   - اگر به متدها یا Properties خاصی از این مدل‌ها نیاز باشد، ایمپورت در داخل متد
#     (Lazy Import) انجام می‌شود یا از django.apps.apps.get_model استفاده می‌کنیم.

User = get_user_model()


# --- انتخاب‌های وضعیت خدمت ---

class ReceptionServiceStatus(models.Model):
    """
    وضعیت‌های مختلف یک خدمت در پذیرش (در صف، در حال انجام، تمام شده و ...)
    با قابلیت ثبت زمان شروع، زمان پایان، کاربر ایجادکننده، و مدت‌زمان.
    """

    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("started", "در حال انجام"),
        ("completed", "اتمام یافته"),
        ("canceled", "لغو شده"),
        ("rejected", "رد شده"),
        ("on_hold", "در انتظار ادامه"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="وضعیت خدمت"
    )

    reception_service = models.ForeignKey(
        "ReceptionService",
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="خدمت مربوطه"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )

    changed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="تغییر یافته توسط"
    )

    duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="مدت این وضعیت (ثانیه)"
    )

    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="یادداشت اپراتور"
    )

    class Meta:
        ordering = ["timestamp"]
        verbose_name = "وضعیت خدمت"
        verbose_name_plural = "وضعیت‌های خدمت"

    def __str__(self):
        return f"{self.reception_service} - {self.status} @ {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    def save(self, *args, **kwargs):
        """
        در لحظه‌ی ذخیره اگر وضعیت قبلی وجود داشته باشد،
        مدت زمان آن را محاسبه می‌کنیم و در آن وضعیت قبلی ذخیره می‌کنیم.
        """
        super().save(*args, **kwargs)  # ابتدا خودش ذخیره شود

        # به‌روزرسانی وضعیت قبلی
        previous = (
            ReceptionServiceStatus.objects
            .filter(reception_service=self.reception_service)
            .exclude(pk=self.pk)
            .order_by("-timestamp")
            .first()
        )

        if previous and previous.duration_seconds == 0:
            delta = (self.timestamp - previous.timestamp).total_seconds()
            previous.duration_seconds = max(1, int(delta))  # حداقل ۱ ثانیه
            previous.save(update_fields=["duration_seconds"])

        # به‌روزرسانی فیلد latest_status در مدل ReceptionService
        if self.reception_service.latest_status != self.status:
            self.reception_service.latest_status = self.status
            self.reception_service.save(update_fields=["latest_status"])

    # ======================
    # 🔍 متدهای کمکی
    # ======================

    @classmethod
    def create(cls, reception_service, status, user=None, note=None):
        """
        متد ساخت سریع یک وضعیت جدید برای یک خدمت
        """
        return cls.objects.create(
            reception_service=reception_service,
            status=status,
            changed_by=user,
            note=note,
        )

    @staticmethod
    def get_last_status(reception_service):
        """
        دریافت آخرین وضعیت ثبت‌شده برای یک خدمت
        """
        return (
            ReceptionServiceStatus.objects
            .filter(reception_service=reception_service)
            .order_by("-timestamp")
            .first()
        )

    @staticmethod
    def get_status_durations(reception_service):
        """
        لیست تمام وضعیت‌ها به همراه مدت زمان هر کدام
        """
        return (
            ReceptionServiceStatus.objects
            .filter(reception_service=reception_service)
            .values("status")
            .annotate(total_duration=models.Sum("duration_seconds"))
            .order_by("status")
        )

    @staticmethod
    def get_total_duration(reception_service):
        """
        مدت زمان کل چرخه یک خدمت از زمان در صف تا پایان
        """
        qs = ReceptionServiceStatus.objects.filter(reception_service=reception_service)
        if not qs.exists():
            return 0

        start = qs.order_by("timestamp").first().timestamp
        end = qs.order_by("-timestamp").first().timestamp
        return int((end - start).total_seconds())


### **📍 مدل شعبه (Location)**

class Location(models.Model):
    """
    مدل Location برای تعریف و مدیریت شعب مختلف کلینیک یا بیمارستان.
    """
    name = models.CharField("نام شعبه", max_length=255, unique=True,
                            help_text="نام منحصر به فرد برای هر شعبه (مثال: شعبه مرکزی).")
    address = models.TextField("آدرس کامل", blank=True, null=True,
                               help_text="آدرس پستی کامل شعبه.")
    phone_number = models.CharField("شماره تماس شعبه", max_length=20, blank=True, null=True,
                                    help_text="شماره تماس اصلی شعبه.")
    email = models.EmailField("ایمیل شعبه", blank=True, null=True,
                              help_text="آدرس ایمیل برای ارتباط با شعبه.")
    is_active = models.BooleanField("فعال", default=True,
                                    help_text="آیا این شعبه در حال حاضر فعال و قابل استفاده است؟")

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "شعبه"
        verbose_name_plural = "شعب"
        ordering = ["name"]
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


### **🗄️ مدل منبع (Resource)**

class Resource(models.Model):
    """
    مدل Resource برای تعریف و مدیریت منابع فیزیکی یا پرسنلی مورد نیاز برای خدمات و نوبت‌ها.
    """
    RESOURCE_TYPES = [
        ('room', 'اتاق'),
        ('equipment', 'تجهیزات'),
        ('staff', 'پرسنل کمکی'),
        ('other', 'سایر'),
    ]

    name = models.CharField("نام منبع", max_length=255,
                            help_text="نام یا شناسه منبع (مثال: اتاق ۱، دستگاه سونوگرافی).")
    type = models.CharField("نوع منبع", max_length=50, choices=RESOURCE_TYPES,
                            help_text="دسته بندی نوع منبع (مثال: اتاق، تجهیزات).")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="شعبه مرتبط", blank=True, null=True,
                                 help_text="شعبه‌ای که این منبع در آن قرار دارد.")
    description = models.TextField("توضیحات منبع", blank=True, null=True,
                                   help_text="جزئیات بیشتر درباره منبع.")
    is_available = models.BooleanField("در دسترس", default=True,
                                       help_text="آیا این منبع در حال حاضر قابل استفاده و قابل رزرو است؟")

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "منبع"
        verbose_name_plural = "منابع"
        ordering = ["location", "name"]
        unique_together = ('name', 'location',)
        indexes = [
            models.Index(fields=['name', 'location']),
            models.Index(fields=['type']),
            models.Index(fields=['is_available']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) در {self.location.name}"


### **پذیرش (Reception)**

class Reception(models.Model):
    """
    مدل Reception نماینده یک رویداد پذیرش بیمار در کلینیک.
    هر پذیرش می‌تواند شامل یک یا چند خدمت (ReceptionService) باشد.
    """
    SOURCE_CHOICES = [
        ("phone", "تلفنی"),
        ("online", "آنلاین"),
        ("in_person", "حضوری"),
        ("referral", "ارجاعی"),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, null=True, verbose_name="منبع پذیرش",
                              help_text="نحوه آغاز فرآیند پذیرش (مثلاً تماس تلفنی، مراجعه حضوری).")
    patient = models.ForeignKey("patient.Patient", on_delete=models.PROTECT, verbose_name="بیمار",
                                related_name="receptions",
                                help_text="بیماری که این پذیرش برای او انجام شده است.")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name="شعبه پذیرش", blank=True, null=True,
                                 help_text="شعبه‌ای که این پذیرش در آن انجام شده است.")

    admission_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ پذیرش",
                                          help_text="تاریخ و زمان دقیق پذیرش بیمار.")
    admission_code = models.CharField(max_length=30, unique=True, verbose_name="کد پذیرش",
                                      help_text="کد یکتا برای هر پذیرش جهت پیگیری آسان.")

    referring_doctor_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام پزشک ارجاع‌دهنده",
                                             help_text="نام پزشک خارجی که بیمار را ارجاع داده است.")
    referring_center_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام مرکز ارجاع‌دهنده",
                                             help_text="نام مرکز درمانی/تشخیصی که بیمار را ارجاع داده است.")

    consent_obtained = models.BooleanField(default=False, verbose_name="رضایت‌نامه دریافت شد؟",
                                           help_text="آیا رضایت‌نامه لازم از بیمار (یا ولی او) دریافت شده است؟")
    attached_documents = models.FileField(upload_to="reception_docs/", null=True, blank=True,
                                          verbose_name="فایل‌های پیوست",
                                          help_text="فایل‌های ضمیمه مرتبط با پذیرش (مثلاً معرفی‌نامه).")

    wait_time_minutes = models.PositiveIntegerField(blank=True, null=True, verbose_name="مدت زمان انتظار (دقیقه)",
                                                    help_text="مدت زمان انتظار بیمار از ورود تا شروع اولین خدمت.")

    debit_transaction = models.ForeignKey(
        "accounting.Transaction", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reception_debit",
        verbose_name="تراکنش بدهکاری پذیرش",
        help_text="تراکنش بدهکاری اصلی مرتبط با این پذیرش (مثلاً پرداخت هزینه)."
    )
    credit_transaction = models.ForeignKey(
        "accounting.Transaction", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reception_credit",
        verbose_name="تراکنش بستانکاری پذیرش",
        help_text="تراکنش بستانکاری اصلی مرتبط با این پذیرش (مثلاً بازپرداخت)."
    )

    receptionist = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="مسئول پذیرش",
                                     help_text="کاربری که این پذیرش را ثبت کرده است.")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌های پذیرش",
                             help_text="یادداشت‌ها و توضیحات اضافی برای این پذیرش.")

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        ordering = ["-admission_date"]
        verbose_name = "پذیرش"
        verbose_name_plural = "پذیرش‌ها"
        indexes = [
            models.Index(fields=["admission_date"]),
            models.Index(fields=["location"]),
            models.Index(fields=["admission_code"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        patient_info = self.patient.full_name() if self.patient else "بیمار نامشخص"
        location_info = self.location.name if self.location else "شعبه نامشخص"
        return f"پذیرش {self.admission_code} - {patient_info} در {location_info} - {self.admission_date.strftime('%Y/%m/%d %H:%M')}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        from apps.reception.utils import generate_admission_code

        if not self.admission_code:
            self.admission_code = generate_admission_code()

        super().save(*args, **kwargs)

        if is_new and self.patient:
            self.patient.total_receptions = Reception.objects.filter(patient=self.patient).count()
            self.patient.save(update_fields=["total_receptions"])

    @property
    def total_cost(self):
        """جمع کل هزینه‌های تمامی خدمات مرتبط با این پذیرش."""
        return sum(service.cost for service in self.services.all() if service.cost is not None)

    @property
    def total_paid_amount(self):
        """مجموع مبالغ پرداخت شده برای این پذیرش (از طریق فاکتورهای مرتبط)."""
        from apps.accounting.models import Invoice
        invoices = Invoice.objects.filter(related_reception=self)
        return sum(invoice.paid_amount for invoice in invoices)

    @property
    def total_debt(self):
        """مجموع بدهی‌های باقی‌مانده برای این پذیرش."""
        return max(self.total_cost - self.total_paid_amount, 0)

    @property
    def all_services_done(self):
        """آیا تمامی خدمات مرتبط با این پذیرش (به جز کنسلی) انجام شده‌اند؟"""
        if not self.services.exists():
            return True
        return all(service.status == "done" for service in self.services.all() if service.status != "cancelled")

    @property
    def has_pending_services(self):
        """آیا خدمتی در وضعیت 'در انتظار' یا 'در حال انجام' وجود دارد؟"""
        return self.services.filter(status__in=["pending", "in_progress", "paused"]).exists()

    def get_absolute_url(self):
        return reverse('reception:detail', kwargs={'pk': self.pk})


### **آمار خدمات بیمار (PatientServiceStats)**

class PatientServiceStats(models.Model):
    """
    مدل PatientServiceStats: آمار تعداد دفعات دریافت هر نوع خدمت توسط یک بیمار.
    """
    patient = models.ForeignKey("patient.Patient", on_delete=models.CASCADE, related_name="service_stats",
                                verbose_name="بیمار")
    service_type = models.ForeignKey("ServiceType", on_delete=models.CASCADE, verbose_name="نوع خدمت")
    count = models.PositiveIntegerField(default=0, verbose_name="تعداد دفعات پذیرش/دریافت خدمت")

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        unique_together = ("patient", "service_type")
        verbose_name = "آمار خدمت بیمار"
        verbose_name_plural = "آمار خدمات بیماران"
        indexes = [
            models.Index(fields=['patient', 'service_type']),
        ]

    def __str__(self):
        patient_full_name = self.patient.full_name() if self.patient else "بیمار نامشخص"
        return f"{patient_full_name} - {self.service_type.name}: {self.count}"


### **خدمت پذیرش شده (ReceptionService)**

class ReceptionService(models.Model):
    """
    مدل ReceptionService: نماینده یک خدمت خاص که در چارچوب یک پذیرش به بیمار ارائه می‌شود.
    """
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE, related_name="services", verbose_name="پذیرش",
                                  help_text="پذیرشی که این خدمت در آن انجام شده است.")
    tariff = models.ForeignKey("ServiceTariff", on_delete=models.PROTECT, verbose_name="تعرفه خدمت",
                               help_text="تعرفه خدمت انتخاب شده برای این مورد (برای هزینه).")

    cost = models.PositiveIntegerField(null=True, blank=True, verbose_name="هزینه خدمت (ریال)",
                                       help_text="هزینه این خدمت در زمان ثبت پذیرش.")
    tracking_code = models.CharField(max_length=30, unique=True, editable=False, verbose_name="کد پیگیری",
                                     help_text="کد یکتا برای پیگیری این خدمت خاص.")

    scheduled_time = models.DateTimeField(blank=True, null=True, verbose_name="زمان برنامه‌ریزی‌شده",
                                          help_text="تاریخ و زمان دقیق برنامه‌ریزی شده برای انجام این خدمت.")
    estimated_duration = models.DurationField(blank=True, null=True,
                                              verbose_name="مدت تقریبی",
                                              help_text="مدت زمان تقریبی مورد نیاز برای این خدمت (کپی شده از نوع خدمت).")

    performed_by_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name="performed_services", verbose_name="انجام‌دهنده خدمت",
                                           help_text="کاربری که این خدمت را انجام داده است (پزشک یا پرسنل).")

    done_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان انجام",
                                   help_text="تاریخ و زمان دقیق اتمام خدمت.")
    service_notes = models.TextField(blank=True, null=True, verbose_name="یادداشت خدمت",
                                     help_text="یادداشت‌های خاص برای این خدمت (مثلاً جزئیات انجام).")

    cancel_reason = models.TextField(blank=True, null=True, verbose_name="دلیل کنسلی",
                                     help_text="دلیل لغو شدن این خدمت.")
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان کنسلی",
                                        help_text="تاریخ و زمان دقیق کنسلی خدمت.")

    notification_sent = models.BooleanField(default=False, verbose_name="پیامک ارسال شده؟",
                                            help_text="آیا پیامک/اعلان مربوط به این خدمت ارسال شده است؟")

    service_index = models.PositiveIntegerField(null=True, blank=True, verbose_name="شماره نوبت در پذیرش",
                                                help_text="ترتیب این خدمت در بین خدمات یک پذیرش.")

    latest_status = models.CharField(
        max_length=20,
        choices=ReceptionServiceStatus.STATUS_CHOICES,
        default="pending",
        verbose_name="آخرین وضعیت"
    )

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False,
                                   verbose_name="کاربر ایجادکننده",
                                   help_text="کاربری که این خدمت را در سیستم ثبت کرده است.")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    appointment = models.ForeignKey("appointments.Appointment", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="reception_services", verbose_name="نوبت رزرو شده",
                                    help_text="نوبت رزرو شده‌ای که این خدمت واقعی به آن مربوط است (اختیاری).")

    class Meta:
        ordering = ["-scheduled_time", "-created_at"]
        verbose_name = "خدمت پذیرش شده"
        verbose_name_plural = "خدمات پذیرش شده"
        indexes = [
            models.Index(fields=["tracking_code"]),
            models.Index(fields=["scheduled_time"]),
            models.Index(fields=["reception"]),
            models.Index(fields=["appointment"]),
            models.Index(fields=["tariff"]),
        ]

    def __str__(self):
        patient_full_name = self.reception.patient.full_name() if self.reception and self.reception.patient else "بیمار نامشخص"
        return f"{self.tariff.service_type.name} | {patient_full_name} | وضعیت: {self.get_status_display()}"

    @property
    def calculated_cost(self):
        """هزینه این خدمت بر اساس تعرفه."""
        return self.tariff.amount if self.tariff else None

    @property
    def final_cost(self):
        """هزینه نهایی این خدمت پس از اعمال بیمه و تخفیف."""
        if self.tariff:
            if self.tariff.insurance_coverage:
                return self.tariff.amount * (100 - self.tariff.insurance_coverage) / 100
            return self.tariff.amount
        return 0

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        from apps.reception.utils import generate_service_index_and_code

        if not self.tracking_code:
            if self.tariff and self.tariff.service_type:
                self.service_index, self.tracking_code = generate_service_index_and_code(self.tariff.service_type)

        if self.status == "done" and not self.done_at:
            self.done_at = timezone.now()
            # 📌 جدید: اگر خدمت مربوط به یک نوبت باشد و این آخرین خدمت آن نوبت است، وضعیت نوبت را هم به‌روز کن
            if self.appointment:
                all_related_services_done = all(
                    s.status == "done" for s in self.appointment.reception_services.all() if s.pk != self.pk
                ) and self.status == "done"

                if (not self.appointment.reception_services.exclude(pk=self.pk).exists() and self.status == "done") or \
                        all_related_services_done:
                    from apps.appointments.models import Appointment  # Lazy Import
                    appointment_obj = Appointment.objects.get(pk=self.appointment.pk)
                    appointment_obj.complete_service(user=self.created_by)

        elif self.status == "cancelled" and not self.cancelled_at:
            self.cancelled_at = timezone.now()
            if self.appointment and self.appointment.status not in ['canceled', 'no_show', 'rejected']:
                from apps.appointments.models import Appointment  # Lazy Import
                appointment_obj = Appointment.objects.get(pk=self.appointment.pk)
                appointment_obj.cancel(reason=self.cancel_reason, user=self.created_by)
        elif self.status == "rejected" and not self.cancelled_at:
            self.cancelled_at = timezone.now()
            if self.appointment and self.appointment.status not in ['canceled', 'no_show', 'rejected']:
                from apps.appointments.models import Appointment  # Lazy Import
                appointment_obj = Appointment.objects.get(pk=self.appointment.pk)
                appointment_obj.reject(reason=self.cancel_reason, user=self.created_by)

        if self.tariff and self.tariff.service_type and self.tariff.service_type.duration_minutes is not None:
            self.estimated_duration = timezone.timedelta(minutes=self.tariff.service_type.duration_minutes)

        super().save(*args, **kwargs)

        if self.reception and self.reception.patient and self.tariff and self.tariff.service_type:
            stat, created = PatientServiceStats.objects.get_or_create(
                patient=self.reception.patient,
                service_type=self.tariff.service_type
            )
            stat.count = ReceptionService.objects.filter(
                reception__patient=self.reception.patient,
                tariff__service_type=self.tariff.service_type,
                latest_status__in=["started", "completed"]
            ).count()
            stat.save(update_fields=["count"])

    @property
    def status(self):
        if not self.pk:
            return "pending"
        last_status = self.status_history.order_by("-timestamp").first()
        return last_status.status if last_status else "pending"

    def is_pending(self):
        return self.status == "pending"

    def is_completed(self):
        return self.status == "completed"


class ServiceType(models.Model):
    """
    مدل ServiceType: تعریف انواع خدمات پزشکی قابل ارائه در کلینیک.
    """
    code = models.CharField(max_length=50, unique=True, verbose_name="کد خدمت",
                            help_text="کد یکتا برای شناسایی نوع خدمت (مثال: VZT برای ویزیت).")
    name = models.CharField(max_length=100, verbose_name="نام خدمت",
                            help_text="نام کامل خدمت (مثال: ویزیت پزشک عمومی).")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات خدمت")
    model_path = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="مسیر مدل رکورد تخصصی",
        help_text="به صورت 'apps.ecg.models.ECGRecord'. برای اتصال داینامیک."
    )
    assigned_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_types",
        verbose_name="نقش مسئول خدمت",
        help_text="نقشی که مسئول رسیدگی به این خدمت است و اعلان مربوطه را دریافت می‌کند."
    )

    updates_enabled = models.BooleanField(default=True, verbose_name="به‌روزرسانی لحظه‌ای فعال است؟")

    is_active = models.BooleanField(default=True, verbose_name="فعال؟",
                                    help_text="آیا این نوع خدمت در حال حاضر فعال و قابل ارائه است؟")

    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="مدت زمان خدمت (دقیقه)",
        help_text="مدت زمان تقریبی مورد نیاز برای این خدمت (به دقیقه). برای محاسبه پایان نوبت استفاده می‌شود."
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False,
                                   verbose_name="کاربر ایجادکننده")

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        ordering = ["name"]
        verbose_name = "نوع خدمت"
        verbose_name_plural = "انواع خدمات"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class ServiceTariff(models.Model):
    """
    مدل ServiceTariff: تعریف تعرفه (هزینه) برای هر نوع خدمت.
    """
    service_type = models.ForeignKey("ServiceType", on_delete=models.CASCADE, verbose_name="نوع خدمت")
    amount = models.BigIntegerField(verbose_name="هزینه (تومان)",
                                    help_text="مبلغ هزینه این خدمت به تومان.")
    valid_from = models.DateField(blank=True, null=True, verbose_name="شروع اعتبار",
                                  help_text="تاریخ شروع اعتبار این تعرفه (اختیاری).")
    valid_to = models.DateField(blank=True, null=True, verbose_name="پایان اعتبار",
                                help_text="تاریخ پایان اعتبار این تعرفه (اختیاری).")
    insurance_coverage = models.PositiveIntegerField(blank=True, null=True, verbose_name="پوشش بیمه‌ای (٪)",
                                                     help_text="درصد پوشش بیمه‌ای برای این خدمت (اختیاری).")
    is_active = models.BooleanField(default=True, verbose_name="فعال؟",
                                    help_text="آیا این مبلغ  در حال حاضر فعال و قابل ارائه است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False,
                                   verbose_name="کاربر ایجادکننده")

    # # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        ordering = ["service_type", "-valid_from"]
        verbose_name = "تعرفه خدمت"
        verbose_name_plural = "تعرفه‌های خدمات"
        indexes = [
            models.Index(fields=["service_type"]),
            models.Index(fields=["valid_from", "valid_to"]),
        ]

    def __str__(self):
        try:
            return f"{self.service_type.name} ({intcomma(self.amount)} تومان)"

        except:
            return f"تعرفه #{self.pk}"

    def is_currently_active(self):
        """بررسی می‌کند که آیا این تعرفه در تاریخ جاری فعال است یا خیر."""
        today = timezone.now().date()
        return (not self.valid_from or self.valid_from <= today) and \
            (not self.valid_to or self.valid_to >= today)
