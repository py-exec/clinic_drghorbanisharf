# apps/ecg/urls.py

from django.urls import path

from . import views

app_name = "ecg"

urlpatterns = [
    # ------------------ داشبورد کاری (Worklist) ------------------
    # [GET] - نمایش داشبورد کاری نوار قلب (ECG)
    path("worklist/", views.ecg_worklist_view, name="ecg_worklist"),

    # ------------------ لیست و مدیریت گزارش‌های ECG ------------------

    # [GET] - نمایش لیست تمام گزارش‌های نوار قلب (آرشیو)
    path("archive/", views.ECGRecordListView.as_view(), name="ecg_list"), # Changed name from ecg-report-list

    # [GET, POST] - ایجاد یک گزارش ECG جدید برای یک خدمت پذیرش مشخص
    # استفاده از service_id برای اتصال به ReceptionService
    path("create/for-service/<int:service_id>/", views.ECGRecordCreateView.as_view(), name="ecg_create"),

    # [GET] - مشاهده جزئیات یک گزارش ECG خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.ECGRecordDetailView.as_view(), name="ecg_detail"), # Changed name from ecg-detail

    # [GET, POST] - ویرایش یک گزارش ECG خاص
    path("<int:pk>/update/", views.ECGRecordUpdateView.as_view(), name="ecg_update"), # Changed name from ecg-update

    # [POST] - حذف یک گزارش ECG خاص
    path("<int:pk>/delete/", views.ECGRecordDeleteView.as_view(), name="ecg_delete"), # Changed name from ecg-delete

    # ------------------ URL های کمکی (Partial Views) ------------------
    # این URL برای بارگذاری بخشی از صفحه (مثلا جدول) با استفاده از HTMX یا Ajax است.
    path("partial/table/", views.ecg_table_partial, name="ecg_table_partial"), # Changed name
]