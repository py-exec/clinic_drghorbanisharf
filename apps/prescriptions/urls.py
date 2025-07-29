# apps/prescriptions/urls.py

from django.urls import path

from . import views

app_name = "prescriptions"

urlpatterns = [
    # ------------------ مدیریت نظرات پزشک / نسخه‌ها ------------------

    # [GET] - نمایش لیست تمام نظرات و نسخه‌ها
    # URL اصلی منو: 'prescriptions:doctor-review-list'
    path("", views.doctor_review_list, name="doctor-review-list"),

    # [GET, POST] - ایجاد یک نظر/نسخه جدید برای یک بیمار مشخص
    path("create/for-patient/<int:patient_id>/", views.doctor_review_create, name="doctor-review-create"),

    # [GET] - مشاهده جزئیات یک نظر/نسخه خاص با استفاده از شناسه آن (pk)
    path("<int:pk>/", views.doctor_review_detail, name="doctor-review-detail"),

    # [GET, POST] - ویرایش یک نظر/نسخه خاص
    path("<int:pk>/update/", views.doctor_review_update, name="doctor-review-update"),

    # [POST] - حذف یک نظر/نسخه خاص
    path("<int:pk>/delete/", views.doctor_review_delete, name="doctor-review-delete"),
]
