# apps/tte/urls.py

from django.urls import path

from . import views

app_name = "tte"

urlpatterns = [
    # ------------------ لیست و مدیریت گزارش‌های TTE ------------------

    # [GET] - نمایش لیست تمام گزارش‌های اکوکاردیوگرافی از راه قفسه سینه
    # این URL می‌تواند به منوی "خدمات کلینیکی" اضافه شود.
    path("", views.echo_tte_list, name="tte_list"),

    # [GET, POST] - ایجاد یک گزارش TTE جدید برای یک بیمار مشخص
    path("create/for-patient/<int:patient_id>/", views.echo_create_tte_for_patient, name="tte_create"),

    # [GET] - مشاهده جزئیات یک گزارش TTE خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.tte_report_detail, name="tte_detail"),

    # [GET, POST] - ویرایش یک گزارش TTE خاص
    path("<int:pk>/update/", views.tte_report_update, name="tte_update"),

    # [POST] - حذف یک گزارش TTE خاص
    path("<int:pk>/delete/", views.tte_report_delete, name="tte_delete"),
]
