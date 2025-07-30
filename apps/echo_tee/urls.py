# apps/echo_tee/urls.py

from django.urls import path

from . import views

app_name = "echo_tee" # Changed app_name for consistency with folder name

urlpatterns = [
    # ------------------ داشبورد کاری (Worklist) ------------------
    # [GET] - نمایش داشبورد کاری اکو از راه مری (TEE)
    path("worklist/", views.echo_tee_worklist_view, name="tee_worklist"),

    # ------------------ لیست و مدیریت گزارش‌های TEE ------------------

    # [GET] - نمایش لیست تمام گزارش‌های اکو از راه مری (آرشیو)
    path("archive/", views.TEEEchoReportListView.as_view(), name="tee_list"),

    # [GET, POST] - ایجاد یک گزارش TEE جدید برای یک خدمت پذیرش مشخص
    # استفاده از service_id برای اتصال به ReceptionService
    path("create/for-service/<int:service_id>/", views.TEEEchoReportCreateView.as_view(), name="tee_create"),

    # [GET] - مشاهده جزئیات یک گزارش TEE خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.TEEEchoReportDetailView.as_view(), name="tee_detail"),

    # [GET, POST] - ویرایش یک گزارش TEE خاص
    path("<int:pk>/update/", views.TEEEchoReportUpdateView.as_view(), name="tee_update"),

    # [POST] - حذف یک گزارش TEE خاص
    path("<int:pk>/delete/", views.TEEEchoReportDeleteView.as_view(), name="tee_delete"),
]