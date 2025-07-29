# apps/reception/utils.py

from django.core.cache import cache
from django.utils import timezone

from .models import ReceptionService, ServiceTariff, Reception

# ✅ این باید مثل مدل باشه تا prefix پایه شماره نوبت رو مشخص کنه
SERVICE_INDEX_PREFIX = {
    "ecg": 1000,
    "tee": 2000,
    "tte": 3000,
    "stress": 4000,
    "tilt": 5000,
    "holter": 6000,
    "procedure": 7000,
    "doctor_review": 8000,
}


def generate_admission_code():
    """
    تولید کد پذیرش یکتا و مرتب با فرمت: ADM-250717-0004
    از Redis کش برای افزایش سرعت در تولید شماره‌های متوالی استفاده می‌کند.
    """
    now = timezone.now()
    date_part = now.strftime("%y%m%d")
    prefix = "ADM"
    base_code = f"{prefix}-{date_part}"

    # کلید کش برای شمارنده امروز
    cache_key = f"last_admission_code:{base_code}"
    last_known_number = cache.get(cache_key)

    if last_known_number is not None:
        new_number = last_known_number + 1
    else:
        # اگر در کش نبود، آخرین شماره را از دیتابیس بخوان
        last_reception = Reception.objects.filter(
            admission_code__startswith=base_code
        ).order_by('admission_code').last()

        if last_reception:
            try:
                last_number = int(last_reception.admission_code.split('-')[-1])
            except (ValueError, IndexError):
                last_number = 0
        else:
            last_number = 0
        new_number = last_number + 1

    # ذخیره شماره جدید در کش برای استفاده‌های بعدی (یک روز اعتبار)
    cache.set(cache_key, new_number, timeout=86400)

    return f"{base_code}-{new_number:04d}"


def generate_service_index_and_code(service_type_obj, date=None):
    """
    تولید شماره نوبت و کد پیگیری هماهنگ.
    """
    date = date or timezone.now()
    today_str = date.strftime("%y%m%d")
    prefix = service_type_obj.code[:3].upper() if service_type_obj.code else "SVC"

    # 👈 اصلاح کوئری برای شمارش صحیح
    count = ReceptionService.objects.filter(
        tariff__service_type=service_type_obj,
        created_at__date=date.date()
    ).count() + 1

    # فرض بر این است که SERVICE_INDEX_PREFIX در بالای فایل تعریف شده
    base = SERVICE_INDEX_PREFIX.get(service_type_obj.code, 9000)
    service_index = base + count
    tracking_code = f"{prefix}-{today_str}-{service_index}"

    return service_index, tracking_code


def get_tariff_cached(service_type_obj):
    """
    دریافت تعرفه از کش (اگر نبود، از دیتابیس و ذخیره در کش).
    """
    if not service_type_obj:
        return 0

    key = f"tariff:{service_type_obj.code}"
    tariff_amount = cache.get(key)

    if tariff_amount is None:
        # 👈 اصلاح کوئری برای یافتن تعرفه فعال
        tariff_obj = ServiceTariff.objects.filter(
            service_type=service_type_obj
        ).order_by("-valid_from").first()  # فرض بر اینکه جدیدترین تعرفه، معتبرترین است

        if tariff_obj and tariff_obj.is_active():
            tariff_amount = tariff_obj.amount
            cache.set(key, tariff_amount, timeout=3600)  # 1 ساعت
        else:
            tariff_amount = 0
            # اگر تعرفه فعالی یافت نشد، نتیجه صفر را برای مدت کوتاهی کش کن
            cache.set(key, 0, timeout=600)

    return tariff_amount
