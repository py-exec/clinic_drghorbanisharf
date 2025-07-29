import datetime
import uuid
from apps.doctors.models import Doctor, DoctorSchedule, BlockTime, \
    Specialty  # Specialty هم برای WaitingListEntry نیاز است
# 📌 ایمپورت‌های ضروری از اپ‌های دیگر
from apps.patient.models import Patient
from apps.reception.models import ServiceType, Location, Resource, ReceptionService
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords

User = settings.AUTH_USER_MODEL  # استفاده مستقیم از User model


### **🔁 مدل سری نوبت‌های تکراری (RecurringAppointmentSeries)**

class RecurringAppointmentSeries(models.Model):
    """
    مدل RecurringAppointmentSeries: برای مدیریت مجموعه‌ای از نوبت‌های تکراری.
    این مدل نوبت‌های دوره‌ای را به عنوان یک "سری" واحد گروه‌بندی می‌کند.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="بیمار",
                                help_text="بیمار مربوط به این سری نوبت‌ها.")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="پزشک مرتبط",
                               help_text="پزشک اصلی برای این سری نوبت‌ها (اختیاری).")
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="نوع خدمت",
                                     help_text="نوع خدمتی که در این سری ارائه می‌شود.")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="شعبه اصلی",
                                 help_text="شعبه اصلی برای این سری نوبت‌ها.")

    # جزئیات تکرار
    RECURRENCE_CHOICES = [
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('bi_weekly', 'دو هفته یکبار'),
        ('monthly', 'ماهانه'),
        ('yearly', 'سالانه'),
        ('custom', 'سفارشی'),
    ]
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, verbose_name="نوع تکرار",
                                       help_text="نوع تکرار نوبت‌ها (مثلاً هفتگی، ماهانه).")
    recurrence_value = models.CharField(max_length=50, blank=True, null=True, verbose_name="مقدار تکرار",
                                        help_text="مقدار مرتبط با نوع تکرار (مثلاً '0,2,4' برای شنبه، دوشنبه، چهارشنبه؛ یا '15' برای پانزدهم هر ماه).")

    start_date = models.DateField(verbose_name="تاریخ شروع سری",
                                  help_text="تاریخ شروع اولین نوبت از این سری.")
    end_date = models.DateField(blank=True, null=True, verbose_name="تاریخ پایان سری",
                                help_text="تاریخ پایان آخرین نوبت از این سری (اختیاری، می‌تواند نامحدود باشد).")
    # num_occurrences = models.PositiveIntegerField(blank=True, null=True, verbose_name="تعداد تکرارها",
    #                                               help_text="تعداد دفعات تکرار نوبت (اختیاری، اگر پایان سری بر اساس تعداد باشد).")

    # وضعیت سری
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('paused', 'متوقف'),
        ('completed', 'تکمیل شده'),
        ('canceled', 'لغو شده'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="وضعیت سری",
                              help_text="وضعیت فعلی سری نوبت‌های تکراری.")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="created_recurring_series", verbose_name="ثبت کننده")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "سری نوبت تکراری"
        verbose_name_plural = "سری‌های نوبت تکراری"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        patient_name = self.patient.user.get_full_name() if self.patient and self.patient.user else "بیمار نامشخص"
        doctor_name = self.doctor.user.get_full_name() if self.doctor and self.doctor.user else "پزشک نامشخص"
        return f"سری تکراری: {patient_name} با {doctor_name} ({self.get_recurrence_type_display()})"

    def clean(self):
        super().clean()
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("تاریخ پایان سری نمی‌تواند قبل از تاریخ شروع باشد.")
        # Add more validation for recurrence_value based on recurrence_type (e.g., '0,2,4' for weekly)

    def get_absolute_url(self):
        # در آینده می‌توانید یک صفحه جزئیات برای سری‌های تکراری بسازید
        return reverse('appointments:appointment_calendar')


### **📝 مدل ورود لیست انتظار (WaitingListEntry)**

class WaitingListEntry(models.Model):
    """
    مدل WaitingListEntry: برای ثبت بیماران در لیست انتظار نوبت‌دهی.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="بیمار",
                                help_text="بیمار در لیست انتظار.")

    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="پزشک مورد نظر",
                               help_text="پزشک مورد نظر برای نوبت (اختیاری).")
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="نوع خدمت مورد نظر",
                                     help_text="نوع خدمت مورد نظر (اختیاری).")
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="تخصص مورد نظر",
                                  help_text="تخصص مورد نظر پزشک (اختیاری، در صورت عدم انتخاب پزشک خاص).")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="شعبه مورد نظر",
                                 help_text="شعبه مورد نظر برای نوبت (اختیاری).")

    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت بیمار",
                             help_text="توضیحات یا ملاحظات اضافی از طرف بیمار.")

    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('offered', 'نوبت پیشنهاد شده'),
        ('booked', 'نوبت رزرو شد'),
        ('canceled', 'لغو شده'),
        ('expired', 'منقضی شده'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت",
                              help_text="وضعیت فعلی درخواست در لیست انتظار.")

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)
    offered_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان پیشنهاد نوبت",
                                      help_text="زمانی که نوبتی به بیمار پیشنهاد شده است.")
    assigned_appointment = models.OneToOneField('Appointment', on_delete=models.SET_NULL, null=True, blank=True,
                                                related_name='waiting_list_source',  # این نام related_name خودشه
                                                verbose_name="نوبت رزرو شده",
                                                help_text="نوبتی که از طریق این درخواست لیست انتظار رزرو شده است.")

# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "ورودی لیست انتظار"
        verbose_name_plural = "ورودی‌های لیست انتظار"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
            models.Index(fields=['service_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        patient_name = self.patient.user.get_full_name() if self.patient and self.patient.user else "بیمار نامشخص"
        doctor_name_or_service = ""
        if self.doctor and self.doctor.user:
            doctor_name_or_service = f"دکتر {self.doctor.user.get_full_name()}"
        elif self.service_type:
            doctor_name_or_service = f"خدمت {self.service_type.name}"
        elif self.specialty:
            doctor_name_or_service = f"تخصص {self.specialty.title}"
        else:
            doctor_name_or_service = "نامشخص"
        return f"لیست انتظار: {patient_name} برای {doctor_name_or_service} - وضعیت: {self.get_status_display()}"

    def clean(self):
        super().clean()
        if not (self.doctor or self.service_type or self.specialty):
            raise ValidationError(
                "برای ثبت در لیست انتظار، باید حداقل یک 'پزشک مورد نظر'، 'نوع خدمت مورد نظر' یا 'تخصص مورد نظر' مشخص شود."
            )
        if self.doctor and self.specialty and self.doctor.specialty != self.specialty:
            raise ValidationError(
                "تخصص انتخابی با تخصص پزشک مورد نظر همخوانی ندارد."
            )

    def get_absolute_url(self):
        # در آینده می‌توانید یک صفحه جزئیات برای لیست انتظار بسازید
        return reverse('appointments:appointment_calendar')


### **📅 مدل نوبت (Appointment)**

class Appointment(models.Model):
    """
    مدل Appointment: جامع و انعطاف‌پذیر برای مدیریت نوبت‌ها در سطح Enterprise.
    """

    # --- ۱. ارتباطات اصلی موجودیت‌ها ---
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, verbose_name="بیمار",
                                help_text="بیماری که نوبت برای او رزرو شده است.")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, verbose_name="پزشک",
                               help_text="پزشکی که نوبت با او رزرو شده است.")
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, verbose_name="نوع خدمت",
                                     help_text="نوع خدمتی که در این نوبت ارائه می‌شود.")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name="شعبه",
                                 help_text="شعبه‌ای که نوبت در آن برگزار می‌شود.")
    resources = models.ManyToManyField(Resource, blank=True, verbose_name="منابع مورد نیاز",
                                       help_text="منابع (مانند اتاق، تجهیزات) که برای این نوبت رزرو شده‌اند.")

    # --- ۲. جزئیات زمان‌بندی نوبت ---
    date = models.DateField(verbose_name="تاریخ نوبت", help_text="تاریخ برنامه‌ریزی شده برای نوبت.")
    time = models.TimeField(verbose_name="ساعت شروع نوبت", help_text="ساعت شروع نوبت (مثلاً ۰۹:۰۰).")
    end_time = models.TimeField(blank=True, null=True, verbose_name="ساعت پایان نوبت",
                                help_text="ساعت پایان نوبت (بر اساس مدت زمان خدمت محاسبه می‌شود).")

    estimated_duration_minutes = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="مدت زمان تخمینی (دقیقه)",
        help_text="مدت زمان تخمینی برای این نوبت (کپی شده از نوع خدمت).")
    actual_duration_minutes = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="مدت زمان واقعی (دقیقه)",
        help_text="مدت زمان واقعی که نوبت طول کشید (پس از انجام)."
    )

    # --- ۳. وضعیت و چرخه حیات نوبت ---
    METHOD_CHOICES = [
        ('phone', 'تلفنی'),
        ('in_person', 'حضوری'),
        ('online', 'آنلاین'),
        ('walk_in', 'مراجعه فوری'),
    ]
    method = models.CharField(max_length=50, choices=METHOD_CHOICES, default='online', verbose_name="نحوه پذیرش",
                              help_text="روشی که بیمار برای نوبت اقدام کرده است.")

    STATUS_CHOICES = [
        ('pending', 'در انتظار تأیید'),
        ('booked', 'رزرو شده'),
        ('confirmed', 'تایید شده'),
        ('check_in', 'حضور یافته'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'انجام شده'),
        ('canceled', 'لغو شده'),
        ('no_show', 'عدم حضور'),
        ('rescheduled', 'تغییر زمان داده شده'),
        ('rejected', 'رد شده'),
        ('pending_payment', 'در انتظار پرداخت'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='booked', verbose_name="وضعیت نوبت",
                              help_text="وضعیت فعلی این نوبت در چرخه حیات آن.")

    status_changed_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان آخرین تغییر وضعیت",
                                             help_text="آخرین زمان تغییر وضعیت نوبت.")

    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="دلیل لغو/رد",
                                           help_text="دلیل لغو شدن نوبت یا رد شدن آن.")
    reschedule_count = models.PositiveIntegerField(default=0, verbose_name="تعداد دفعات تغییر زمان",
                                                   help_text="تعداد دفعاتی که این نوبت تغییر زمان داده است.")
    previous_appointment = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True,
                                                related_name='rescheduled_to_appointment',
                                                verbose_name="نوبت قبلی (در صورت تغییر زمان)",
                                                help_text="اگر این نوبت از تغییر زمان یک نوبت دیگر ایجاد شده باشد.")

    # --- ۴. کدهای رهگیری و شناسه ---
    tracking_code = models.CharField(max_length=100, unique=True, editable=False, null=True, blank=True,
                                     verbose_name="کد رهگیری یکتا",
                                     help_text="کد یکتا برای پیگیری این نوبت توسط بیمار یا منشی.")

    # --- ۵. نوبت‌های تکراری (Recurring Appointments) ---
    is_recurrent = models.BooleanField(default=False, verbose_name="نوبت تکراری",
                                       help_text="آیا این نوبت بخشی از یک سری نوبت‌های تکراری است؟")
    # 📌 فیلد فعال شده: ارتباط با مدل RecurringAppointmentSeries
    recurring_series = models.ForeignKey(RecurringAppointmentSeries, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='appointments',
                                         verbose_name="سری نوبت‌های تکراری اصلی",
                                         help_text="ارجاع به سری نوبت‌های تکراری که این نوبت عضوی از آن است.")

    # --- ۶. فیلدهای مدیریتی و آماری برای جریان کار ---
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="created_appointments", verbose_name="ثبت کننده",
                                   help_text="کاربری که این نوبت را ثبت کرده است.")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین به‌روزرسانی")

    # زمان‌های کلیدی در چرخه مراجعه بیمار
    check_in_time = models.DateTimeField(blank=True, null=True, verbose_name="زمان ورود به کلینیک",
                                         help_text="زمانی که بیمار برای این نوبت وارد کلینیک شده است.")
    service_start_time = models.DateTimeField(blank=True, null=True, verbose_name="زمان شروع واقعی خدمت",
                                              help_text="زمانی که ارائه خدمت به بیمار عملاً آغاز شده است.")
    service_end_time = models.DateTimeField(blank=True, null=True, verbose_name="زمان پایان واقعی خدمت",
                                            help_text="زمانی که ارائه خدمت به بیمار عملاً به پایان رسیده است.")

    # یادداشت‌ها و ملاحظات
    patient_notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌های بیمار",
                                     help_text="یادداشت‌ها یا درخواست‌های خاصی که بیمار ممکن است داشته باشد.")
    internal_notes = models.TextField(blank=True, null=True, verbose_name="یادداشت‌های داخلی سیستم/ادمین",
                                      help_text="یادداشت‌ها و توضیحات برای استفاده داخلی پرسنل (مثلاً پیگیری).")

    # 📌 فیلد مدیریت صف انتظار و اولویت
    priority_number = models.PositiveIntegerField(blank=True, null=True, verbose_name="شماره اولویت/صف",
                                                  help_text="شماره نوبت در صف برای همان زمان و پزشک/خدمت.")

    # --- ۷. ردیابی تاریخچه تغییرات ---
# # HISTORICAL_COMMENTED:     history = HistoricalRecords()

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        ordering = ["date", "time"]
        indexes = [
            models.Index(fields=['doctor', 'date', 'time', 'end_time']),
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['location', 'date', 'status']),
            models.Index(fields=['tracking_code']),
            models.Index(fields=['status', 'date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['date', 'status', 'location', 'doctor']),
        ]
        # اعتبارسنجی تداخل به متد `clean()` این مدل و فرم‌های مرتبط با آن منتقل شده است.

    def save(self, *args, **kwargs):
        # --- ۱. تولید کد رهگیری یکتا ---
        if not self.tracking_code:
            self.tracking_code = str(uuid.uuid4())

        # --- ۲. محاسبه end_time و کپی estimated_duration_minutes ---
        if self.service_type and self.service_type.duration_minutes is not None and self.date and self.time:
            self.estimated_duration_minutes = self.service_type.duration_minutes
            start_datetime_combined = datetime.datetime.combine(self.date, self.time)
            end_datetime_calculated = start_datetime_combined + datetime.timedelta(
                minutes=self.service_type.duration_minutes)
            self.end_time = end_datetime_calculated.time()
        else:
            self.end_time = None
            self.estimated_duration_minutes = None

        # --- ۳. به‌روزرسانی status_changed_at در صورت تغییر وضعیت ---
        if self.pk:
            try:
                old_appointment = Appointment.objects.get(pk=self.pk)
                if old_appointment.status != self.status:
                    self.status_changed_at = timezone.now()
            except Appointment.DoesNotExist:
                pass
        elif not self.status_changed_at:
            self.status_changed_at = timezone.now()

        super().save(*args, **kwargs)

    def clean(self):
        """
        این متد برای اعتبارسنجی‌های پیچیده‌تر که نیاز به دسترسی به دیتابیس دارند، استفاده می‌شود.
        شامل بررسی تداخل نوبت‌ها با پزشک، منابع، شیفت‌های کاری و بلاک‌های زمانی.
        این اعتبارسنجی قبل از ذخیره در دیتابیس (مثلاً هنگام استفاده از فرم‌های جنگو) اجرا می‌شود.
        """
        super().clean()

        # --- ۱. اعتبارسنجی وجود فیلدهای ضروری ---
        if not all([self.patient, self.doctor, self.service_type, self.location, self.date, self.time]):
            raise ValidationError("تمام فیلدهای اصلی (بیمار، پزشک، نوع خدمت، شعبه، تاریخ، زمان) باید پر شوند.")

        # --- ۲. اعتبارسنجی منطقی زمان‌ها ---
        if self.end_time and self.time >= self.end_time:
            raise ValidationError("ساعت شروع نوبت نمی‌تواند بزرگتر یا مساوی ساعت پایان باشد.")

        # --- ۳. بررسی تداخل با شیفت‌های کاری پزشک (`DoctorSchedule`) ---
        day_of_week = self.date.weekday()  # Monday is 0, Sunday is 6
        persian_day_of_week = (day_of_week + 2) % 7  # برای تطبیق با DAY_OF_WEEK_CHOICES در DoctorSchedule

        if not DoctorSchedule.objects.filter(
                doctor=self.doctor,
                location=self.location,
                day_of_week=persian_day_of_week,
                is_active=True,
                start_time__lte=self.time,
                end_time__gte=self.end_time if self.end_time else self.time
        ).exists():
            raise ValidationError(
                f"پزشک {self.doctor.user.get_full_name()} در تاریخ {self.date} و ساعت {self.time} در شعبه {self.location.name} شیفت کاری فعال ندارد یا این نوبت کاملاً در شیفت او قرار نمی‌گیرد."
            )

        # --- ۴. بررسی تداخل با بلاک‌های زمانی (`BlockTime`) ---
        app_start_dt = timezone.make_aware(datetime.datetime.combine(self.date, self.time))
        app_end_dt = timezone.make_aware(datetime.datetime.combine(self.date, self.end_time)) \
            if self.end_time else app_start_dt + timezone.timedelta(minutes=self.service_type.duration_minutes or 30)

        conflicting_blocks_query = Q(
            start_datetime__lt=app_end_dt,
            end_datetime__gt=app_start_dt,
        )

        if BlockTime.objects.filter(conflicting_blocks_query, doctor=self.doctor).exists():
            raise ValidationError(
                f"این نوبت با یک بلاک زمانی (مرخصی، جلسه و...) برای پزشک {self.doctor.user.get_full_name()} تداخل دارد."
            )

        if BlockTime.objects.filter(conflicting_blocks_query, location=self.location).exists():
            raise ValidationError(
                f"این نوبت با یک بلاک زمانی عمومی برای شعبه {self.location.name} تداخل دارد."
            )

        for resource in self.resources.all():
            if BlockTime.objects.filter(conflicting_blocks_query, resource=resource).exists():
                raise ValidationError(
                    f"این نوبت با یک بلاک زمانی برای منبع '{resource.name}' تداخل دارد."
                )

        # --- ۵. بررسی تداخل با نوبت‌های موجود دیگر (`Appointment`) ---
        active_statuses = ['booked', 'confirmed', 'in_progress', 'pending_payment', 'check_in']

        if Appointment.objects.filter(
                doctor=self.doctor,
                date=self.date,
                time__lt=self.end_time,
                end_time__gt=self.time,
                status__in=active_statuses
        ).exclude(pk=self.pk if self.pk else None).exists():
            raise ValidationError(
                f"پزشک {self.doctor.user.get_full_name()} در تاریخ {self.date} از ساعت {self.time} تا {self.end_time} قبلاً نوبت دیگری دارد. لطفاً زمان دیگری را انتخاب کنید."
            )

        if self.resources.exists():
            conflicting_appointments_by_resource = Appointment.objects.filter(
                date=self.date,
                time__lt=self.end_time,
                end_time__gt=self.time,
                status__in=active_statuses
            ).exclude(pk=self.pk if self.pk else None)

            for resource in self.resources.all():
                if conflicting_appointments_by_resource.filter(resources=resource).exists():
                    raise ValidationError(
                        f"منبع '{resource.name}' در تاریخ {self.date} از ساعت {self.time} تا {self.end_time} قبلاً برای نوبت دیگری رزرو شده است. لطفاً زمان دیگری را انتخاب کنید یا منبع دیگری را انتخاب کنید."
                    )

        # --- ۶. بررسی ظرفیت پزشک (اختیاری) ---
        if Appointment.objects.filter(doctor=self.doctor, date=self.date, status__in=active_statuses).count() >= 20:
            raise ValidationError(
                f"پزشک {self.doctor.user.get_full_name()} در تاریخ {self.date} به حداکثر ظرفیت نوبت‌دهی رسیده است.")

    # --- ۷. متدهای کمکی برای نمایش، گزارش‌گیری و تحلیل آماری ---
    @property
    def patient_full_name(self):
        """نام کامل بیمار."""
        return self.patient.user.get_full_name() if self.patient and self.patient.user else "بیمار نامشخص"

    @property
    def doctor_full_name(self):
        """نام کامل پزشک."""
        return self.doctor.user.get_full_name() if self.doctor and self.doctor.user else "پزشک نامشخص"

    @property
    def service_name(self):
        """نام نوع خدمت."""
        return self.service_type.name if self.service_type else "خدمت نامشخص"

    @property
    def location_name(self):
        """نام شعبه."""
        return self.location.name if self.location else "شعبه نامشخص"

    @property
    def calendar_title(self):
        """عنوان نوبت برای نمایش در نمای تقویم (FullCalendar)."""
        return f"{self.patient_full_name} ({self.service_name})"

    @property
    def get_full_start_datetime(self):
        """تاریخ و زمان شروع نوبت را به صورت یک شیء datetime آگاه (aware) برمی‌گرداند."""
        return timezone.make_aware(datetime.datetime.combine(self.date, self.time))

    @property
    def get_full_end_datetime(self):
        """تاریخ و زمان پایان نوبت را به صورت یک شیء datetime آگاه (aware) برمی‌گرداند."""
        if self.end_time:
            return timezone.make_aware(datetime.datetime.combine(self.date, self.end_time))
        return self.get_full_start_datetime + timezone.timedelta(minutes=self.estimated_duration_minutes or 30)

    @property
    def is_past_appointment(self):
        """بررسی می‌کند که آیا نوبت در گذشته است."""
        now = timezone.now()
        full_start_dt = self.get_full_start_datetime
        return full_start_dt < now and self.status not in ['completed', 'canceled', 'no_show', 'rescheduled',
                                                           'rejected']

    @property
    def time_to_appointment(self):
        """زمان باقی‌مانده تا نوبت یا زمان سپری شده از نوبت (Duration object)."""
        now = timezone.now()
        full_start_dt = self.get_full_start_datetime
        if full_start_dt > now:
            return full_start_dt - now
        else:
            return now - full_start_dt

    @property
    def wait_time_minutes(self):
        """محاسبه زمان انتظار بیمار در کلینیک (Check-in تا شروع واقعی خدمت)."""
        if self.check_in_time and self.service_start_time:
            delta = self.service_start_time - self.check_in_time
            return int(delta.total_seconds() / 60)
        return None

    @property
    def service_delivery_duration_minutes(self):
        """مدت زمان واقعی ارائه خدمت (شروع واقعی تا پایان واقعی خدمت)."""
        if self.service_start_time and self.service_end_time:
            delta = self.service_end_time - self.service_start_time
            return int(delta.total_seconds() / 60)
        return None

    @property
    def no_show_rate(self):
        """
        نکته: این یک property برای کل کلاس نیست، بلکه یک محاسبه آماری است.
        برای محاسبه نرخ عدم حضور، باید QuerySet از نوبت‌ها را فیلتر کنید.
        مثلاً: Appointment.objects.filter(status='no_show').count() / Appointment.objects.filter(date__lte=timezone.now().date()).count()
        """
        return None

    # --- ۸. متدهای مدیریت وضعیت و عملیات (برای استفاده در Views/API) ---
    def confirm(self, user: User = None):
        """تغییر وضعیت نوبت به 'تایید شده'."""
        if self.status in ['pending', 'booked', 'pending_payment']:
            old_status = self.status
            self.status = 'confirmed'
            self.save(update_fields=['status'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='confirmed')
            # ارسال اعلان تایید به بیمار (با استفاده از CommunicationApp)
            return True
        return False

    def check_in(self, user: User = None):
        """ثبت ورود بیمار به کلینیک و تغییر وضعیت به 'حضور یافته'."""
        if self.status in ['booked', 'confirmed', 'pending_payment']:
            old_status = self.status
            self.status = 'check_in'
            self.check_in_time = timezone.now()
            self.save(update_fields=['status', 'check_in_time'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='check_in')
            # شاید اعلان برای پزشک که بیمار حضور یافته
            return True
        return False

    def start_service(self, user: User = None):
        """ثبت شروع واقعی خدمت و تغییر وضعیت به 'در حال انجام'."""
        if self.status in ['check_in', 'confirmed']:
            old_status = self.status
            self.status = 'in_progress'
            self.service_start_time = timezone.now()
            self.save(update_fields=['status', 'service_start_time'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='in_progress')
            return True
        return False

    def complete_service(self, user: User = None, actual_duration_minutes: int = None):
        """تکمیل نوبت، ثبت مدت زمان واقعی و تغییر وضعیت به 'انجام شده'."""
        if self.status in ['in_progress', 'check_in', 'confirmed', 'booked']:
            old_status = self.status
            self.status = 'completed'
            self.service_end_time = timezone.now()
            if actual_duration_minutes is not None:
                self.actual_duration_minutes = actual_duration_minutes
            elif self.service_start_time:
                delta = self.service_end_time - self.service_start_time
                self.actual_duration_minutes = int(delta.total_seconds() / 60)
            self.save(update_fields=['status', 'service_end_time', 'actual_duration_minutes'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='completed')
            return True
        return False

    def cancel(self, reason: str = None, user: User = None):
        """لغو نوبت."""
        if self.status not in ['completed', 'canceled', 'no_show', 'rejected']:
            old_status = self.status
            self.status = 'canceled'
            self.cancellation_reason = reason
            self.save(update_fields=['status', 'cancellation_reason'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='canceled')
            return True
        return False

    def mark_no_show(self, user: User = None):
        """ثبت عدم حضور بیمار."""
        if self.status not in ['completed', 'canceled', 'no_show', 'rejected']:
            old_status = self.status
            self.status = 'no_show'
            self.save(update_fields=['status'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='no_show')
            return True
        return False

    def reject(self, reason: str = None, user: User = None):
        """رد نوبت (مثلاً توسط پزشک در پورتال خود)."""
        if self.status in ['pending', 'booked']:
            old_status = self.status
            self.status = 'rejected'
            self.cancellation_reason = reason
            self.save(update_fields=['status', 'cancellation_reason'])
            self.history.create(user=user, field='status', old_value=old_status, new_value='rejected')
            return True
        return False

    def reschedule(self, new_date: datetime.date, new_time: datetime.time, user: User = None):
        """
        تغییر زمان نوبت. این متد یک نوبت جدید ایجاد می‌کند و نوبت فعلی را به 'rescheduled' تغییر می‌دهد.
        منطق پیچیده اعتبارسنجی تداخل باید قبل از فراخوانی این متد انجام شود.
        """
        if self.status not in ['completed', 'canceled', 'no_show', 'rejected']:
            old_status = self.status
            self.status = 'rescheduled'
            self.reschedule_count += 1
            self.save(update_fields=['status', 'reschedule_count'])

            new_appointment = Appointment.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                service_type=self.service_type,
                location=self.location,
                date=new_date,
                time=new_time,
                method=self.method,
                created_by=user if user else self.created_by,
                previous_appointment=self
            )
            new_appointment.resources.set(self.resources.all())
            return new_appointment
        return None

    def get_absolute_url(self):
        """
        آدرس کانونیکال (صفحه جزئیات) این نوبت را برمی‌گرداند.
        چون صفحه جزئیات مجزا نداریم، به تقویم بازمی‌گردیم.
        """
        return reverse('appointments:appointment_calendar')
