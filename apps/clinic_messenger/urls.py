# apps/clinic_messenger/urls.py

from django.urls import path

from . import views_sms, views_email

app_name = "clinic_messenger"

urlpatterns = [
    # ------------------ پیامک (SMS) ------------------
    path("sms/dashboard/", views_sms.sms_dashboard_view, name="sms_dashboard"),
    path("sms/send/", views_sms.sms_send_view, name="sms_send"),
    path("sms/send/bulk/", views_sms.sms_send_bulk_view, name="sms_send_bulk"),
    path("sms/status/", views_sms.sms_status_view, name="sms_status"),
    path("sms/test-pattern/", views_sms.test_pattern_view, name="test_pattern"),

    # --- مدیریت کامل تنظیمات SMS ---
    path("sms/configs/create/", views_sms.SMSConfigCreateView.as_view(), name="sms_config_create"),
    path("sms/configs/<int:pk>/update/", views_sms.SMSConfigUpdateView.as_view(), name="sms_config_update"),
    path("sms/configs/<int:pk>/delete/", views_sms.SMSConfigDeleteView.as_view(), name="sms_config_delete"),

    # --- مدیریت کامل پترن‌های SMS ---
    path("sms/patterns/", views_sms.SMSPatternListView.as_view(), name="sms_pattern_list"),
    path("sms/patterns/create/", views_sms.SMSPatternCreateView.as_view(), name="sms_pattern_create"),
    path("sms/patterns/<int:pk>/update/", views_sms.SMSPatternUpdateView.as_view(), name="sms_pattern_update"),
    path("sms/patterns/<int:pk>/delete/", views_sms.SMSPatternDeleteView.as_view(), name="sms_pattern_delete"),

    # 👈 جدید: URL های مدیریت انواع پترن
    path("sms/pattern-types/", views_sms.SMSPatternTypeListView.as_view(), name="sms_pattern_type_list"),
    path("sms/pattern-types/create/", views_sms.SMSPatternTypeCreateView.as_view(), name="sms_pattern_type_create"),
    path("sms/pattern-types/<int:pk>/update/", views_sms.SMSPatternTypeUpdateView.as_view(),
         name="sms_pattern_type_update"),
    path("sms/pattern-types/<int:pk>/delete/", views_sms.SMSPatternTypeDeleteView.as_view(),
         name="sms_pattern_type_delete"),

    # ------------------ ایمیل (Email) ------------------
    # path("email/send/", views_email.email_send_view, name="email_send"),
    # path("email/status/", views_email.email_status_view, name="email_status"),
    #
    # path("email/configs/", views_email.EmailConfigListView.as_view(), name="email_config_list"),
    # path("email/configs/create/", views_email.EmailConfigCreateView.as_view(), name="email_config_create"),
    # path("email/configs/<int:pk>/update/", views_email.EmailConfigUpdateView.as_view(), name="email_config_update"),
    # path("email/configs/<int:pk>/delete/", views_email.EmailConfigDeleteView.as_view(), name="email_config_delete"),
]
