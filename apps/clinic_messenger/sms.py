import requests
from django.conf import settings
from ippanel import Client
from ippanel.errors import Error as IPPanelError
from typing import Dict, Optional

from .models import SMSConfig, SMSPattern


# ──────────────────────────────────────────────
# دریافت تنظیم فعال
# ──────────────────────────────────────────────
def get_active_sms_config() -> Optional[SMSConfig]:
    return SMSConfig.objects.filter(is_active=True).order_by("-updated_at").first()


# ──────────────────────────────────────────────
# وضعیت اتصال پنل پیامک
# ──────────────────────────────────────────────
def get_ippanel_status(config: SMSConfig) -> dict:
    config = get_active_sms_config()
    if not config:
        return {
            "success": False,
            "provider": None,
            "message": "⚠️ تنظیمات فعال برای پنل پیامک پیدا نشد.",
        }

    try:
        client = Client(config.api_key)
        credit = client.get_credit()
        return {
            "success": True,
            "provider": config.provider,
            "credit": credit,
            "message": f"💰 موجودی: {credit:,.0f} ریال – شماره ارسال‌کننده: {config.originator}",
        }
    except IPPanelError as e:
        return {
            "success": False,
            "provider": config.provider,
            "message": f"❌ خطای پنل: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "provider": config.provider,
            "message": f"❌ خطای غیرمنتظره: {str(e)}",
        }


# ──────────────────────────────────────────────
# ارسال پیامک مستقیم (تستی یا واقعی)
# ──────────────────────────────────────────────
# ──────────────────────────────────────────────
# ارسال پیامک مستقیم (تستی یا واقعی)
# ──────────────────────────────────────────────
def send_sms(to: str, text: str) -> dict:
    config = get_active_sms_config()
    if not config:
        return {
            "success": False,
            "message": "❌ تنظیمات فعال پیامک موجود نیست.",
            "response": None,
        }

    try:
        client = Client(config.api_key)
        # ⚠️ IPPanel: متد send به ترتیب شماره فرستنده، گیرنده و متن رو می‌گیره
        message_id = client.send(
            config.originator,  # شماره فرستنده
            [to],  # گیرنده (لیست)
            text  # متن پیام
        )
        return {
            "success": True,
            "message": "✅ ارسال موفق بود.",
            "response": {"message_id": message_id},
        }

    except IPPanelError as e:
        return {
            "success": False,
            "message": f"❌ خطای IPPanel: {str(e)}",
            "response": None,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ خطای غیرمنتظره: {str(e)}",
            "response": None,
        }


# ──────────────────────────────────────────────
# ارسال پیامک با پترن (از مدل SMSPattern)
# ──────────────────────────────────────────────
def send_sms_pattern(to: str, pattern_code: str, variables: Dict[str, str]) -> dict:
    config = get_active_sms_config()
    if not config:
        return {
            "success": False,
            "message": "❌ تنظیمات فعال پیامک موجود نیست.",
            "response": None,
        }

    try:
        client = Client(config.api_key)
        message_id = client.send_pattern(
            pattern_code,  # 👈 کد پترن
            config.originator,  # 👈 شماره فرستنده
            to,  # 👈 شماره گیرنده
            variables  # 👈 متغیرهای پترن
        )
        return {
            "success": True,
            "message": f"✅ ارسال موفق بود. کد پیام: {message_id}",
            "response": None
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"❌ خطا در ارسال پیامک: {str(e)}",
            "response": None
        }
