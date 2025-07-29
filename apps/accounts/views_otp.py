# apps/accounts/views_otp.py

import random
from datetime import timedelta
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import OTPCode, User


# from ..clinic_messenger.sms import send_sms_pattern # 👈 موقتا کامنت شد تا وابستگی حذف شود
# from ..clinic_messenger.models import SMSMessage # 👈 موقتا کامنت شد


# ----------------------------
# ارسال کد تأیید (OTP)
# ----------------------------
@csrf_exempt
@require_POST
def send_otp_view(request):
    phone = request.POST.get("phone")
    purpose = request.POST.get("purpose", "verify")  # اهداف: verify, login, reset, 2fa

    if not phone or not phone.isdigit():
        return HttpResponseBadRequest("شماره موبایل نامعتبر است.")

    # TODO: در آینده می‌توان بر اساس purpose، محدودیت‌های متفاوتی اعمال کرد.
    # مثلا برای ورود، کاربر حتما نباید لاگین باشد.

    # ایجاد کد
    code = str(random.randint(100000, 999999))
    expires = timezone.now() + timedelta(minutes=3)

    OTPCode.objects.create(
        phone_number=phone,
        code=code,
        purpose=purpose,
        expires_at=expires,
    )

    # --- بخش ارسال پیامک (در صورت فعال بودن اپلیکیشن clinic_messenger) ---
    # try:
    #     result = send_sms_pattern(phone, "otp_login", {"code": code})
    #     SMSMessage.objects.create(
    #         to=phone,
    #         body=f"OTP: {code}",
    #         purpose="otp",
    #         status="sent" if result.get("success") else "failed",
    #         response_message=result.get("response")
    #     )
    #     if result.get("success"):
    #         return JsonResponse({"success": True, "message": f"کد تأیید به {phone} ارسال شد."})
    #     else:
    #         return JsonResponse({"success": False, "message": "ارسال پیامک با خطا مواجه شد."}, status=500)
    # except Exception as e:
    #     # لاگ کردن خطا
    #     return JsonResponse({"success": False, "message": "خطای داخلی در سرویس پیامک."}, status=500)
    # --------------------------------------------------------------------

    # پاسخ موقت تا زمان فعال‌سازی سرویس پیامک
    print(f"OTP for {phone}: {code}")  # نمایش کد در کنسول برای تست
    return JsonResponse({"success": True, "message": f"کد تأیید به {phone} ارسال شد (حالت تست)."})


# ----------------------------
# بررسی کد تأیید
# ----------------------------
@csrf_exempt
@require_POST
def verify_otp_view(request):
    phone = request.POST.get("phone")
    code = request.POST.get("code")
    purpose = request.POST.get("purpose", "verify")

    if not all([phone, code]):
        return JsonResponse({"success": False, "message": "شماره یا کد ناقص است."}, status=400)

    try:
        otp = OTPCode.objects.filter(
            phone_number=phone,
            code=code,
            purpose=purpose,
            is_verified=False
        ).latest("created_at")

        if otp.is_expired():
            return JsonResponse({"success": False, "message": "کد منقضی شده است."}, status=410)

        otp.is_verified = True
        otp.save()

        user = User.objects.filter(phone_number=phone, is_active=True).first()

        if purpose == "verify" and user and request.user.is_authenticated and request.user == user:
            user.phone_verified = True
            user.save(update_fields=["phone_verified"])
            return JsonResponse({"success": True, "message": "شماره موبایل شما با موفقیت تأیید شد."})

        elif purpose == "login":
            if user:
                login(request, user)
                user.update_last_seen(request)
                return JsonResponse({"success": True, "message": "ورود موفقیت‌آمیز بود."})
            else:
                return JsonResponse({"success": False, "message": "کاربری با این شماره تلفن یافت نشد."}, status=404)

        elif purpose == "reset":
            # قرار دادن یک فلگ در سشن برای اجازه به کاربر برای تغییر رمز
            request.session["reset_password_phone"] = phone
            return JsonResponse({"success": True, "redirect_url": reverse_lazy("accounts:password_reset_confirm")})

        return JsonResponse({"success": True, "message": "کد با موفقیت تأیید شد."})

    except OTPCode.DoesNotExist:
        return JsonResponse({"success": False, "message": "کد وارد شده نادرست است."}, status=404)
