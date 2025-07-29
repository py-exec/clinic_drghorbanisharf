# apps/tee/urls.py

from django.urls import path

from . import views

app_name = "tee"

urlpatterns = [
    # ------------------ لیست و مدیریت گزارش‌های TEE ------------------

    # [GET] - نمایش لیست تمام گزارش‌های اکوکاردیوگرافی از راه مری
    # این URL می‌تواند به منوی "خدمات کلینیکی" اضافه شود.
    path("", views.echo_tee_list, name="tee_list"),

    # [GET, POST] - ایجاد یک گزارش TEE جدید برای یک بیمار مشخص
    path("create/for-patient/<int:patient_id>/", views.echo_create_tee_for_patient, name="tee_create"),

    # [GET] - مشاهده جزئیات یک گزارش TEE خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.tee_report_detail, name="tee_detail"),

    # [GET, POST] - ویرایش یک گزارش TEE خاص
    path("<int:pk>/update/", views.tee_report_update, name="tee_update"),

    # [POST] - حذف یک گزارش TEE خاص
    path("<int:pk>/delete/", views.tee_report_delete, name="tee_delete"),
]
