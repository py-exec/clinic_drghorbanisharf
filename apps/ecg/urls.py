# apps/ecg/urls.py

from django.urls import path

from . import views

app_name = "ecg"

urlpatterns = [
    # ------------------ لیست و مدیریت گزارش‌های ECG ------------------

    # [GET] - نمایش لیست تمام گزارش‌های نوار قلب
    # URL اصلی منو: 'ecg:ecg-report-list'
    path("", views.ecg_report_list, name="ecg-report-list"),

    # [GET, POST] - ایجاد یک گزارش جدید برای یک بیمار مشخص
    path("create/for-patient/<int:patient_id>/", views.ecg_create_for_patient, name="ecg-create"),

    # [GET] - مشاهده جزئیات یک گزارش خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.ecg_report_detail, name="ecg-detail"),

    # [GET, POST] - ویرایش یک گزارش خاص
    path("<int:pk>/update/", views.ecg_report_update, name="ecg-update"),

    # [POST] - حذف یک گزارش خاص
    path("<int:pk>/delete/", views.ecg_report_delete, name="ecg-delete"),

    # ------------------ URL های کمکی (Partial Views) ------------------
    # این URL برای بارگذاری بخشی از صفحه (مثلا جدول) با استفاده از HTMX یا Ajax است.
    path("partial/table/", views.ecg_table_partial, name="ecg-table-partial"),
]
