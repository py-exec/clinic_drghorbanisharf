from django.contrib import admin

from .models import (
    SMSConfig, SMSPattern, SMSMessage,
    OTPCode, EmailMessage, EmailConfig
)


# ----------------------------
# تنظیمات پیامک
# ----------------------------
@admin.register(SMSConfig)
class SMSConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "originator", "is_active", "updated_at")
    list_filter = ("provider", "is_active")
    search_fields = ("provider", "originator", "api_key")
    ordering = ("-updated_at",)


# ----------------------------
# پترن پیامک
# ----------------------------
@admin.register(SMSPattern)
class SMSPatternAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "provider", "config", "is_active", "created_at")
    list_filter = ("provider", "is_active", "created_at")
    search_fields = ("code", "name", "body_template")
    ordering = ("-created_at",)
    raw_id_fields = ("config",)


# ----------------------------
# پیامک‌ها
# ----------------------------
@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = (
        "to",
        "purpose",
        "status",
        "requested_by",
        "config",
        "created_at",
        "body_short",
    )
    list_filter = ("status", "purpose", "created_at", "config")
    search_fields = ("to", "body")
    ordering = ("-created_at",)
    readonly_fields = (
        "to",
        "body",
        "purpose",
        "status",
        "requested_by",
        "response_message",
        "config",
        "created_at",
    )

    def body_short(self, obj):
        return obj.body[:40] + "..." if len(obj.body) > 40 else obj.body

    body_short.short_description = "متن پیام"


# ----------------------------
# کدهای OTP
# ----------------------------
@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "purpose",
        "code",
        "status",
        "is_verified",
        "requested_by",
        "config",
        "is_expired_display",
        "created_at",
        "expires_at",
    )
    list_filter = ("purpose", "status", "is_verified", "created_at", "config")
    search_fields = ("phone_number", "code")
    ordering = ("-created_at",)
    readonly_fields = (
        "phone_number",
        "purpose",
        "code",
        "status",
        "is_verified",
        "requested_by",
        "config",
        "created_at",
        "expires_at",
    )

    def is_expired_display(self, obj):
        return obj.is_expired()

    is_expired_display.short_description = "منقضی شده؟"
    is_expired_display.boolean = True


# ----------------------------
# ایمیل‌های ارسالی
# ----------------------------
@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = (
        "to_email",
        "purpose",
        "subject_short",
        "status",
        "requested_by",
        "created_at",
    )
    list_filter = ("status", "purpose", "created_at")
    search_fields = ("to_email", "subject", "body")
    ordering = ("-created_at",)
    readonly_fields = (
        "to_email",
        "purpose",
        "subject",
        "body",
        "status",
        "requested_by",
        "response_message",
        "created_at",
    )

    def subject_short(self, obj):
        return obj.subject[:40] + "..." if len(obj.subject) > 40 else obj.subject

    subject_short.short_description = "موضوع"


# ----------------------------
# تنظیمات ایمیل
# ----------------------------
@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "from_email", "host", "port", "is_active", "updated_at")
    list_filter = ("provider", "use_tls", "use_ssl", "is_active")
    search_fields = ("host", "username", "from_email")
    ordering = ("-updated_at",)
