# apps/risk_assessment/models.py
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

User = get_user_model()
# CHOICES for ClinicalAssessment
GENDER_CHOICES = [
    ("", "انتخاب کنید..."),
    ("male", "مرد"),
    ("female", "زن"),
    ("other", "سایر"),
]

CONSCIOUSNESS_CHOICES = [
    ("", "انتخاب کنید..."),
    ("alert", "هوشیار"),
    ("drowsy", "خواب‌آلود"),
    ("stupor", "استوپور"),
    ("coma", "کما"),
]

SMOKING_CHOICES = [
    ("", "انتخاب کنید..."),
    ("never", "هرگز"),
    ("past", "قبلاً"),
    ("current", "در حال حاضر"),
]

ALCOHOL_CHOICES = [
    ("", "انتخاب کنید..."),
    ("never", "هرگز"),
    ("social", "مصرف تفریحی"),
    ("regular", "مصرف منظم"),
]

ACTIVITY_CHOICES = [
    ("", "انتخاب کنید..."),
    ("sedentary", "کم تحرک"),
    ("moderate", "متوسط"),
    ("active", "فعال"),
]

SLEEP_CHOICES = [
    ("", "انتخاب کنید..."),
    ("good", "خوب"),
    ("fair", "متوسط"),
    ("poor", "ضعیف"),
    ("insomnia", "بی‌خوابی"),
]

ECG_CHOICES = [
    ("", "انتخاب کنید..."),
    ("normal_sinus_rhythm", "ریتم سینوسی نرمال"),
    ("afib", "فیبریلاسیون دهلیزی"),
    ("flutter", "فلوتر دهلیزی"),
    ("tachycardia", "تاکی‌کاردی"),
    ("bradycardia", "برادی‌کاردی"),
    ("ischemia", "ایسکمی"),
    ("infarction", "انفارکتوس"),
    ("other", "سایر"),
]

HOLTER_RHYTHM_CHOICES = [
    ("", "انتخاب کنید..."),
    ("normal", "نرمال"),
    ("arrhythmia_detected", "آریتمی تشخیص داده شده"),
    ("afib", "فیبریلاسیون دهلیزی"),
    ("pvc", "PVC"),
    ("pac", "PAC"),
    ("other", "سایر"),
]

HOLTER_BP_CHOICES = [
    ("", "انتخاب کنید..."),
    ("normal", "نرمال"),
    ("htn", "فشار خون بالا"),
    ("hypotension", "فشار خون پایین"),
    ("variable", "متغیر"),
]

ECHO_CHOICES = [
    ("", "انتخاب کنید..."),
    ("normal", "نرمال"),
    ("lvh", "LVH"),
    ("valve_disease", "بیماری دریچه‌ای"),
    ("cardiomyopathy", "کاردیومیوپاتی"),
    ("ef_reduced", "EF کاهش یافته"),
    ("ef_preserved", "EF حفظ شده"),
    ("other", "سایر"),
]

TEE_CHOICES = [
    ("", "انتخاب کنید..."),
    ("normal", "نرمال"),
    ("mass", "توده"),
    ("clot", "لخته"),
    ("asd", "ASD"),
    ("pfo", "PFO"),
    ("valve_abnormality", "ناهنجاری دریچه‌ای"),
    ("other", "سایر"),
]

MI_CHOICES = [
    ("", "انتخاب کنید..."),
    ("no_history", "عدم سابقه"),
    ("old_mi", "MI قدیمی"),
    ("recent_mi", "MI اخیر"),
    ("multiple_mi", "MI متعدد"),
]

HF_CHOICES = [
    ("", "انتخاب کنید..."),
    ("no_hf", "عدم نارسایی قلبی"),
    ("hfref", "HFREF (کاهش یافته)"),
    ("hfpef", "HFPEF (حفظ شده)"),
    ("acute_hf", "نارسایی حاد قلبی"),
]

# CHOICES for DiabetesModule
DIABETES_TYPE_CHOICES = [
    ("", "انتخاب کنید..."),
    ("type1", "نوع ۱"),
    ("type2", "نوع ۲"),
    ("gestational", "بارداری"),
    ("prediabetes", "پیش‌دیابت"),
    ("none", "هیچکدام"),
]

DIABETES_TREATMENT_CHOICES = [
    ("", "انتخاب کنید..."),
    ("diet_exercise", "رژیم غذایی و ورزش"),
    ("oral_meds", "داروهای خوراکی"),
    ("insulin", "انسولین"),
    ("combination", "ترکیبی"),
]

# CHOICES for HypertensionModule
HTN_LEVEL_CHOICES = [
    ("", "انتخاب کنید..."),
    ("normal", "نرمال"),
    ("elevated", "افزایش یافته"),
    ("stage1", "مرحله ۱"),
    ("stage2", "مرحله ۲"),
    ("crisis", "بحران فشار خون"),
]

# CHOICES for ArrhythmiaModule
DIAGNOSED_BY_CHOICES = [
    ("", "انتخاب کنید..."),
    ("ecg", "ECG"),
    ("holter", "هولتر"),
    ("echo", "اکوکاردیوگرافی"),
    ("ep_study", "مطالعه الکتروفیزیولوژی"),
    ("clinical", "بالینی"),
]

SYMPTOMS_CHOICES = [
    ("", "انتخاب کنید..."),
    ("palpitations", "تپش قلب"),
    ("dizziness", "سرگیجه"),
    ("syncope", "سنکوپ"),
    ("chest_pain", "درد قفسه سینه"),
    ("shortness_of_breath", "تنگی نفس"),
    ("asymptomatic", "بدون علامت"),
]

# CHOICES for DeviceInfo
DEVICE_TYPE_CHOICES = [
    ("", "انتخاب کنید..."),
    ("pacemaker", "ضربان‌ساز (Pacemaker)"),
    ("icd", "دفیبریلاتور (ICD)"),
    ("crt_d", "CRT-D"),
    ("crt_p", "CRT-P"),
    ("loop_recorder", "ضبط کننده لوپ (ILR)"),
]
# --- IMPORT ALL CHOICES HERE ---
# from .choices import (GENDER_CHOICES, CONSCIOUSNESS_CHOICES, SMOKING_CHOICES,
#                       ALCOHOL_CHOICES, ACTIVITY_CHOICES, SLEEP_CHOICES,
#                       ECG_CHOICES, HOLTER_RHYTHM_CHOICES, HOLTER_BP_CHOICES,
#                       ECHO_CHOICES, TEE_CHOICES, MI_CHOICES, HF_CHOICES,
#                       DIABETES_TYPE_CHOICES, DIABETES_TREATMENT_CHOICES,
#                       HTN_LEVEL_CHOICES, DIAGNOSED_BY_CHOICES, SYMPTOMS_CHOICES,
#                       DEVICE_TYPE_CHOICES)
# Or define them directly in this file as shown in Step 1.

# Ensure Patient model is imported or in the same file if not separate app
from apps.patient.models import Patient # Assuming patient app and Patient model

class ClinicalAssessment(models.Model):
    """
    مدل اصلی برای ذخیره ارزیابی بالینی بیماران در یک زمان خاص.
    تمام اطلاعات مربوط به یک ویزیت یا ارزیابی خاص بیمار در اینجا یا از طریق روابط به این مدل لینک می‌شوند.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='clinical_assessments',
                                verbose_name="بیمار")
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="ارزیابی کننده",
                                    help_text="پزشک یا کارشناسی که ارزیابی را انجام داده است.")
    assessment_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ و زمان ارزیابی")

    # اطلاعات دموگرافیک (اطلاعات پایه بیمار از Patient گرفته می‌شود)
    # gender might be here if it's specifically observed/confirmed at assessment,
    # otherwise it should be in Patient or User profile.
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="جنسیت")

    # بخش ۲: ارزیابی سلامت (علائم حیاتی و وضعیت بالینی)
    bp = models.CharField(max_length=20, null=True, blank=True, verbose_name="فشار خون (میلی‌متر جیوه)")
    hr = models.IntegerField(null=True, blank=True, verbose_name="ضربان قلب (bpm)")
    spo2 = models.IntegerField(null=True, blank=True, verbose_name="اکسیژن خون (SpO2)")
    temp = models.FloatField(null=True, blank=True, verbose_name="دمای بدن (°C)")
    rr = models.IntegerField(null=True, blank=True, verbose_name="تعداد تنفس در دقیقه")
    consciousness = models.CharField(max_length=50, choices=CONSCIOUSNESS_CHOICES, null=True, blank=True,
                                     verbose_name="وضعیت هوشیاری")
    height = models.FloatField(null=True, blank=True, verbose_name="قد (سانتی‌متر)")
    weight = models.FloatField(null=True, blank=True, verbose_name="وزن (کیلوگرم)")
    bmi = models.FloatField(null=True, blank=True, verbose_name="BMI")

    # بخش ۴: سبک زندگی و عوامل خطر (مربوط به این ارزیابی)
    smoking = models.CharField(max_length=50, choices=SMOKING_CHOICES, null=True, blank=True,
                               verbose_name="استفاده از دخانیات")
    alcohol = models.CharField(max_length=50, choices=ALCOHOL_CHOICES, null=True, blank=True, verbose_name="مصرف الکل")
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, null=True, blank=True,
                                verbose_name="فعالیت فیزیکی روزانه")
    sleep = models.CharField(max_length=50, choices=SLEEP_CHOICES, null=True, blank=True, verbose_name="وضعیت خواب")
    diet = models.TextField(null=True, blank=True, verbose_name="الگوی رژیم غذایی")

    # فیلدهای پرچم برای وجود ماژول‌های مرتبط (به جای تکرار فیلدهای جزئیات)
    # اینها نشان می‌دهند که آیا یک رکورد AngiographyInfo یا DeviceInfo برای این ارزیابی وجود دارد یا خیر.
    # details are in respective OneToOne fields
    # has_angiography = models.BooleanField(default=False, verbose_name="آیا بیمار آنژیوگرافی انجام داده است؟") # Redundant with AngiographyInfo
    # has_device = models.BooleanField(default=False, verbose_name="آیا بیمار دستگاه باطری دارد؟") # Redundant with DeviceInfo

    # نتایج پاراکلینیکی اولیه (انتخاب‌های کلی)
    ecg = models.CharField(max_length=50, choices=ECG_CHOICES, null=True, blank=True, verbose_name="نوار قلب (ECG)")
    holter_rhythm = models.CharField(max_length=50, choices=HOLTER_RHYTHM_CHOICES, null=True, blank=True,
                                     verbose_name="هولتر ریتم")
    holter_bp = models.CharField(max_length=50, choices=HOLTER_BP_CHOICES, null=True, blank=True,
                                 verbose_name="هولتر فشار")
    echo = models.CharField(max_length=50, choices=ECHO_CHOICES, null=True, blank=True, verbose_name="اکو")
    tee = models.CharField(max_length=50, choices=TEE_CHOICES, null=True, blank=True, verbose_name="اکوی تخصصی / TEE")

    # سابقه MI و HF (مربوط به این ارزیابی)
    has_mi = models.CharField(max_length=50, choices=MI_CHOICES, null=True, blank=True,
                              verbose_name="سابقه سکته قلبی (MI)")
    has_heart_failure = models.CharField(max_length=50, choices=HF_CHOICES, null=True, blank=True,
                                         verbose_name="نارسایی قلبی")

    # داروهای OTC، مکمل‌ها، آلرژی دارویی (مربوط به این ارزیابی)
    otc_medications = models.TextField(null=True, blank=True, verbose_name="داروهای OTC / بدون نسخه",
                                       help_text="داروهایی که بدون نسخه پزشک مصرف می‌شوند.")
    supplements = models.TextField(null=True, blank=True, verbose_name="مکمل‌ها / داروهای گیاهی",
                                   help_text="انواع مکمل‌ها یا داروهای گیاهی مصرفی.")
    drug_allergy_assessment = models.TextField(null=True, blank=True, verbose_name="سابقه عدم تحمل دارویی (عوارض / آلرژی) در این ارزیابی",
                                               help_text="آلرژی‌های دارویی گزارش شده در این ارزیابی. (آلرژی‌های کلی بیمار در مدل Patient ثبت می‌شوند.)")


    # خروجی سیستم هوشمند
    brain_output = models.TextField(null=True, blank=True, verbose_name="نتیجه تحلیل سیستم هوشمند",
                                    help_text="این فیلد توسط سیستم هوشمند پر می‌شود.", editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ارزیابی بالینی"
        verbose_name_plural = "ارزیابی‌های بالینی"
        ordering = ['-assessment_date']

    def __str__(self):
        return f"ارزیابی {self.patient.full_name()} در {self.assessment_date.strftime('%Y-%m-%d %H:%M')}"

    # Properties to access patient's user info directly
    @property
    def patient_full_name(self):
        return self.patient.full_name()

    @property
    def patient_national_id(self):
        return self.patient.national_id

    @property
    def patient_date_of_birth(self):
        return self.patient.date_of_birth

    @property
    def patient_record_number(self):
        return self.patient.record_number


class MedicalHistory(models.Model):
    """
    مدلی برای ذخیره سابقه پزشکی و خانوادگی بیمار، مرتبط با یک ارزیابی بالینی خاص.
    این شامل اطلاعات تاریخی است که در زمان ارزیابی جمع آوری شده‌اند.
    """
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='medical_history',
                                      verbose_name="ارزیابی بالینی")

    # این فیلدها اکنون به صورت جزئیات مربوط به این ارزیابی هستند
    chronic_diseases_at_assessment = JSONField(default=list, blank=True,
                                                verbose_name="بیماری‌های مزمن گزارش شده در این ارزیابی")
    surgery_history = models.TextField(null=True, blank=True, verbose_name="سابقه جراحی (گزارش شده در این ارزیابی)")
    last_surgery_date = models.DateField(null=True, blank=True, verbose_name="تاریخ آخرین جراحی")
    hospitalization_history = models.TextField(null=True, blank=True,
                                               verbose_name="سابقه بستری در بیمارستان (گزارش شده در این ارزیابی)")
    # 'allergies' field from your original, now renamed for clarity to avoid confusion with Patient.allergy_info
    # If this is for specific drug allergies reported *at this assessment*, ClinicalAssessment.drug_allergy_assessment is better.
    # If it's general allergies reported at this assessment, and not covered by Patient.allergy_info, keep it.
    # For now, I'm assuming drug_allergy_assessment in ClinicalAssessment handles the allergy aspect.
    # Consider removing this field if ClinicalAssessment.drug_allergy_assessment is sufficient.
    # allergies_reported_at_assessment = models.TextField(null=True, blank=True,
    #                                             verbose_name="آلرژی‌ها / حساسیت‌های گزارش شده در این ارزیابی")
    family_history = models.TextField(null=True, blank=True, verbose_name="سابقه خانوادگی بیماری‌های قلبی یا متابولیک")

    class Meta:
        verbose_name = "سابقه پزشکی (جزئیات ارزیابی)"
        verbose_name_plural = "سوابق پزشکی (جزئیات ارزیابی)"

    def __str__(self):
        return f"سابقه پزشکی برای ارزیابی {self.assessment.id}"


class DiabetesModule(models.Model):
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='diabetes_module',
                                      verbose_name="ارزیابی بالینی")
    diabetes_type = models.CharField(max_length=50, choices=DIABETES_TYPE_CHOICES, null=True, blank=True, verbose_name="نوع دیابت")
    diagnosis_date = models.DateField(null=True, blank=True, verbose_name="تاریخ تشخیص")
    current_treatment = models.CharField(max_length=50, choices=DIABETES_TREATMENT_CHOICES, null=True, blank=True, verbose_name="درمان فعلی")
    medications = JSONField(default=list, blank=True, verbose_name="داروهای مصرفی")
    hba1c = models.FloatField(null=True, blank=True, verbose_name="HbA1c (%)")
    fbs = models.IntegerField(null=True, blank=True, verbose_name="FBS (mg/dL)")
    ppbs = models.IntegerField(null=True, blank=True, verbose_name="PPBS (mg/dL)")
    complications = JSONField(default=list, blank=True, verbose_name="عوارض شناخته‌شده")

    class Meta:
        verbose_name = "ماژول دیابت"
        verbose_name_plural = "ماژول‌های دیابت"

    def __str__(self):
        return f"ماژول دیابت برای ارزیابی {self.assessment.id}"


class HypertensionModule(models.Model):
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='hypertension_module',
                                      verbose_name="ارزیابی بالینی")
    diagnosis_date = models.DateField(null=True, blank=True, verbose_name="تاریخ تشخیص")
    current_level = models.CharField(max_length=50, choices=HTN_LEVEL_CHOICES, null=True, blank=True, verbose_name="سطح فشار خون فعلی")
    avg_home_bp = models.CharField(max_length=20, null=True, blank=True, verbose_name="میانگین فشار خون خانگی")
    resistant_htn = models.BooleanField(null=True, blank=True, verbose_name="فشار مقاوم به درمان")
    medications = JSONField(default=list, blank=True, verbose_name="داروهای مصرفی")
    complications = JSONField(default=list, blank=True, verbose_name="عوارض فشار خون")

    class Meta:
        verbose_name = "ماژول فشار خون"
        verbose_name_plural = "ماژول‌های فشار خون"

    def __str__(self):
        return f"ماژول فشار خون برای ارزیابی {self.assessment.id}"


class ArrhythmiaModule(models.Model):
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='arrhythmia_module',
                                      verbose_name="ارزیابی بالینی")
    arrhythmia_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="نوع آریتمی")
    diagnosed_by = models.CharField(max_length=50, choices=DIAGNOSED_BY_CHOICES, null=True, blank=True, verbose_name="روش تشخیص")
    medications_treatments = JSONField(default=list, blank=True, verbose_name="داروها و درمان‌های انجام‌شده")
    associated_symptoms = models.CharField(max_length=50, choices=SYMPTOMS_CHOICES, null=True, blank=True, verbose_name="علائم همراه")

    class Meta:
        verbose_name = "ماژول آریتمی"
        verbose_name_plural = "ماژول‌های آریتمی"

    def __str__(self):
        return f"ماژول آریتمی برای ارزیابی {self.assessment.id}"


class LabTestResults(models.Model):
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='lab_test_results',
                                      verbose_name="ارزیابی بالینی")
    lab_hba1c = models.FloatField(null=True, blank=True, verbose_name="HbA1c")
    lab_fbs = models.IntegerField(null=True, blank=True, verbose_name="FBS")
    lab_ppbs = models.IntegerField(null=True, blank=True, verbose_name="PPBS")
    lab_ldl = models.IntegerField(null=True, blank=True, verbose_name="LDL")
    lab_hdl = models.IntegerField(null=True, blank=True, verbose_name="HDL")
    lab_chol = models.IntegerField(null=True, blank=True, verbose_name="Chol")
    lab_tg = models.IntegerField(null=True, blank=True, verbose_name="TG")
    lab_cr = models.FloatField(null=True, blank=True, verbose_name="Cr")
    lab_tsh = models.FloatField(null=True, blank=True, verbose_name="TSH")
    lab_hb = models.FloatField(null=True, blank=True, verbose_name="Hb")
    lab_wbc = models.IntegerField(null=True, blank=True, verbose_name="WBC")
    lab_crp = models.FloatField(null=True, blank=True, verbose_name="CRP")
    lab_esr = models.IntegerField(null=True, blank=True, verbose_name="ESR")
    lab_inr = models.FloatField(null=True, blank=True, verbose_name="INR")
    lab_na = models.FloatField(null=True, blank=True, verbose_name="Sodium")
    lab_k = models.FloatField(null=True, blank=True, verbose_name="Potassium")
    lab_ca = models.FloatField(null=True, blank=True, verbose_name="Calcium")

    class Meta:
        verbose_name = "نتیجه آزمایش خون"
        verbose_name_plural = "نتایج آزمایش خون"

    def __str__(self):
        return f"آزمایشات برای ارزیابی {self.assessment.id}"


class DeviceInfo(models.Model):
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='device_info',
                                      verbose_name="ارزیابی بالینی")
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPE_CHOICES, null=True, blank=True, verbose_name="نوع دستگاه")
    brand = models.CharField(max_length=100, null=True, blank=True, verbose_name="مارک دستگاه")
    model = models.CharField(max_length=100, null=True, blank=True, verbose_name="مدل دستگاه")
    serial_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="سریال‌نامبر")
    num_leads = models.IntegerField(null=True, blank=True, verbose_name="تعداد لید (Leads)")
    implant_date = models.DateField(null=True, blank=True, verbose_name="تاریخ کاشت")

    class Meta:
        verbose_name = "اطلاعات دستگاه"
        verbose_name_plural = "اطلاعات دستگاه‌ها"

    def __str__(self):
        return f"اطلاعات دستگاه برای ارزیابی {self.assessment.id}"


class AngiographyInfo(models.Model):
    assessment = models.OneToOneField(ClinicalAssessment, on_delete=models.CASCADE, related_name='angiography_info',
                                      verbose_name="ارزیابی بالینی")
    angiography_date = models.DateField(null=True, blank=True, verbose_name="تاریخ آنژیوگرافی")
    stent_count = models.IntegerField(null=True, blank=True, verbose_name="تعداد استنت‌های کاشته‌شده")
    blocked_vessels = models.CharField(max_length=255, null=True, blank=True, verbose_name="رگ‌های آسیب‌دیده")
    ef_percent = models.FloatField(null=True, blank=True, verbose_name="درصد عملکرد قلب (EF)")

    class Meta:
        verbose_name = "اطلاعات آنژیوگرافی"
        verbose_name_plural = "اطلاعات آنژیوگرافی‌ها"

    def __str__(self):
        return f"اطلاعات آنژیوگرافی برای ارزیابی {self.assessment.id}"


class Medication(models.Model):
    assessment = models.ForeignKey(ClinicalAssessment, on_delete=models.CASCADE, related_name='medications',
                                   verbose_name="ارزیابی بالینی")
    name = models.CharField(max_length=255, verbose_name="نام دارو")
    dose = models.CharField(max_length=100, null=True, blank=True, verbose_name="دوز")
    frequency = models.CharField(max_length=100, null=True, blank=True, verbose_name="تعداد دفعات مصرف")

    class Meta:
        verbose_name = "داروی مصرفی"
        verbose_name_plural = "داروهای مصرفی"

    def __str__(self):
        return f"{self.name} - {self.dose} برای ارزیابی {self.assessment.id}"