# apps/echo_tte/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.contrib.contenttypes.fields import GenericForeignKey # NEW: Import GenericForeignKey
from django.contrib.contenttypes.models import ContentType # NEW: Import ContentType

User = get_user_model()

class TTEEchoReport(models.Model):
    """
    مدل گزارش اکوکاردیوگرافی از راه قفسه سینه (TTE).
    این مدل به عنوان رکورد تخصصی یک خدمت ReceptionService عمل می‌کند.
    """
    # NEW: GenericForeignKey for linking to ReceptionService
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reception_service = GenericForeignKey('content_type', 'object_id')

    # اطلاعات پایه
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="tte_echos", verbose_name="بیمار")
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name="tte_echos", verbose_name="نسخه")
    exam_datetime = models.DateTimeField(verbose_name="تاریخ انجام", default=timezone.now)

    # عملکرد بطن چپ
    ef = models.CharField(max_length=50, blank=True, null=True, verbose_name="کسر تخلیه (EF)")
    lv_dysfunction = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع اختلال عملکرد بطن چپ")
    lvedd = models.CharField(max_length=50, blank=True, null=True, verbose_name="قطر پایانی دیاستول بطن چپ (LVEDD)")
    lvesd = models.CharField(max_length=50, blank=True, null=True, verbose_name="قطر پایانی سیستول بطن چپ (LVESD)")
    gls = models.CharField(max_length=50, blank=True, null=True, verbose_name="کرنش طولی جهانی (GLS)")
    image_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع تصویر")

    # عملکرد بطن راست و فشار ریوی
    tapse = models.CharField(max_length=50, blank=True, null=True, verbose_name="حرکت حلقوی انتهای سیستول بطن راست (TAPSE)")
    spap = models.CharField(max_length=50, blank=True, null=True, verbose_name="فشار سیستولیک شریان ریوی (SPAP)")
    ivc_status = models.CharField(max_length=100, blank=True, null=True, verbose_name="وضعیت ورید اجوف تحتانی (IVC)")

    # دریچه‌ها
    mitral_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع اختلال دریچه میترال")
    mitral_severity = models.CharField(max_length=50, blank=True, null=True, verbose_name="شدت اختلال میترال")
    mitral_features = models.CharField(max_length=50, blank=True, null=True, verbose_name="ویژگی‌های میترال")

    aortic_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع اختلال دریچه آئورت")
    aortic_severity = models.CharField(max_length=50, blank=True, null=True, verbose_name="شدت اختلال آئورت")
    aortic_features = models.CharField(max_length=50, blank=True, null=True, verbose_name="ویژگی‌های آئورت")

    tricuspid_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع اختلال دریچه تری‌کاسپید")
    tricuspid_severity = models.CharField(max_length=50, blank=True, null=True, verbose_name="شدت اختلال تری‌کاسپید")

    pulmonary_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="نوع اختلال دریچه ریوی")
    pulmonary_severity = models.CharField(max_length=50, blank=True, null=True, verbose_name="شدت اختلال ریوی")

    # یافته‌های دیگر
    pericardial_effusion = models.CharField(max_length=50, blank=True, null=True, verbose_name="مایع پریکارد")
    pleural_effusion = models.CharField(max_length=50, blank=True, null=True, verbose_name="مایع پلور")
    mass_or_clot = models.CharField(max_length=50, blank=True, null=True, verbose_name="توده / لخته / ویژتیشن")
    aneurysm = models.CharField(max_length=50, blank=True, null=True, verbose_name="آنوریسم / دیواره غیرطبیعی")

    # کیفیت و شرایط تصویر
    image_quality = models.CharField(max_length=50, blank=True, null=True, verbose_name="کیفیت تصویر")
    image_limitation_reason = models.CharField(max_length=100, blank=True, null=True, verbose_name="علت ضعف کیفیت تصویر")
    probe_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="نوع پروب / تکنیک")
    ecg_sync = models.CharField(max_length=10, blank=True, null=True, verbose_name="هماهنگی با ECG")

    # اطلاعات تکنسین
    patient_cooperation = models.CharField(max_length=50, blank=True, null=True, verbose_name="همکاری بیمار")
    all_views_taken = models.CharField(max_length=10, blank=True, null=True, verbose_name="آیا تمام نماها گرفته شد؟")
    # NEW: Changed technician_name to ForeignKey to User
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tte_technician_reports", verbose_name="نام تکنسین")
    technician_note = models.TextField(blank=True, null=True, verbose_name="توضیحات تکنسین")

    # نظر نهایی پزشک
    need_advanced_echo = models.CharField(max_length=50, blank=True, null=True, verbose_name="نیاز به اکو تخصصی")
    reason_advanced_echo = models.CharField(max_length=100, blank=True, null=True, verbose_name="علت درخواست اکو تخصصی")
    # NEW: Changed reporting_physician to ForeignKey to User
    reporting_physician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tte_reporting_physician_reports", verbose_name="نام پزشک گزارش‌دهنده")
    report_date = models.DateField(blank=True, null=True, verbose_name="تاریخ گزارش")
    final_report = models.TextField(blank=True, null=True, verbose_name="تفسیر نهایی پزشک")

    # فایل پیوست - Consistent naming: use 'upload_file' as in your forms
    upload_file = models.FileField(upload_to="echo/tte/", null=True, blank=True, verbose_name="فایل اکو")

    # اطلاعات ثبت
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ایجادکننده")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "اکوکاردیوگرافی (TTE)"
        verbose_name_plural = "گزارش‌های اکوکاردیوگرافی (TTE)"
        ordering = ["-exam_datetime"]

    def __str__(self):
        return f"TTE برای {self.patient} در {self.exam_datetime.strftime('%Y-%m-%d')}"

    # NEW: Override save to update ReceptionService status and trigger signals
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.full_clean() # Run full validation before saving
        super().save(*args, **kwargs)

        # After saving the TTE report, update the status of the related ReceptionService
        if self.reception_service:
            from apps.reception.status_service import change_service_status # Lazy import
            # If the report is being created, set service status to 'completed'
            # If it's updated, you might want to keep it 'completed' or handle other statuses
            change_service_status(
                self.reception_service,
                'completed', # TTE is a single-stage report, so completing it means service is completed
                user=self.created_by, # Assuming created_by is the appropriate user for status change
                note=f"گزارش اکو (TTE) ثبت/به‌روزرسانی شد. نتیجه نهایی: {self.final_report[:50]}"
            )