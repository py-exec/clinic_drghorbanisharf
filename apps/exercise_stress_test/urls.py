# apps/stress/urls.py

from django.urls import path

from . import views

app_name = "exercise_stress_test"

urlpatterns = [
    # ------------------ لیست و مدیریت گزارش‌های تست ورزش ------------------

    # [GET] - نمایش لیست تمام گزارش‌های تست ورزش
    # این URL می‌تواند به منوی "خدمات کلینیکی" اضافه شود.
    path("", views.stress_test_list, name="stress_list"),

    # [GET, POST] - ایجاد یک گزارش تست ورزش جدید برای یک بیمار مشخص
    path("create/for-patient/<int:patient_id>/", views.stress_test_create, name="stress_create"),

    # [GET] - مشاهده جزئیات یک گزارش تست ورزش خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.stress_report_detail, name="stress_detail"),

    # [GET, POST] - ویرایش یک گزارش تست ورزش خاص
    path("<int:pk>/update/", views.stress_report_update, name="stress_update"),

    # [POST] - حذف یک گزارش تست ورزش خاص
    path("<int:pk>/delete/", views.stress_report_delete, name="stress_delete"),
]
