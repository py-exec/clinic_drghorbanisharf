# apps/tilt/urls.py

from django.urls import path

from . import views

app_name = "tilt"

urlpatterns = [
    # ------------------ داشبورد کاری و لیست‌ها ------------------

    # مسیر جدید: داشبورد اصلی برای تکنسین با لیست انتظار لحظه‌ای
    path("worklist/", views.tilt_worklist_view, name="tilt_worklist"),

    # مسیر آرشیو: لیست تمام گزارش‌های ثبت‌شده و تکمیل‌شده
    path("archive/", views.tilt_test_list, name="tilt_report_archive"),

    # ------------------ مدیریت یک گزارش خاص (CRUD) ------------------

    # ایجاد گزارش برای یک خدمت پذیرش شده
    path("create/for-service/<int:service_id>/", views.tilt_create_view, name="tilt_create"),

    # مشاهده جزئیات یک گزارش
    path("<int:pk>/", views.tilt_test_detail, name="tilt_detail"),

    # ویرایش یک گزارش
    path("<int:pk>/update/", views.tilt_test_update, name="tilt_update"),

    # حذف یک گزارش
    path("<int:pk>/delete/", views.tilt_test_delete, name="tilt_delete"),
]
