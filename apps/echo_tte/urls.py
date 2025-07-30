# apps/echo_tte/urls.py

from django.urls import path

from . import views

app_name = "tte" # The app_name should ideally reflect the app folder name, e.g., "echo_tte"

urlpatterns = [
    # ------------------ داشبورد کاری (Worklist) ------------------
    # [GET] - نمایش داشبورد کاری اکوکاردیوگرافی (TTE)
    path("worklist/", views.echo_tte_worklist_view, name="tte_worklist"),

    # ------------------ لیست و مدیریت گزارش‌های TTE ------------------

    # [GET] - نمایش لیست تمام گزارش‌های اکوکاردیوگرافی از راه قفسه سینه (آرشیو)
    path("archive/", views.TTEEchoReportListView.as_view(), name="tte_list"), # Changed to ListView, name 'tte_list' often implies archive

    # [GET, POST] - ایجاد یک گزارش TTE جدید برای یک خدمت پذیرش مشخص
    # استفاده از service_id برای اتصال به ReceptionService
    path("create/for-service/<int:service_id>/", views.TTEEchoReportCreateView.as_view(), name="tte_create"),

    # اگر همچنان نیاز به ایجاد گزارش مستقیم برای بیمار بدون ReceptionService دارید (کمتر توصیه می‌شود):
    # path("create/for-patient/<int:patient_id>/", views.TTEEchoReportCreateView.as_view(), name="tte_create_for_patient"),

    # [GET] - مشاهده جزئیات یک گزارش TTE خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.TTEEchoReportDetailView.as_view(), name="tte_detail"),

    # [GET, POST] - ویرایش یک گزارش TTE خاص
    path("<int:pk>/update/", views.TTEEchoReportUpdateView.as_view(), name="tte_update"),

    # [POST] - حذف یک گزارش TTE خاص
    path("<int:pk>/delete/", views.TTEEchoReportDeleteView.as_view(), name="tte_delete"),
]