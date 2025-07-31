# apps/prescriptions/urls.py

from django.urls import path

from . import views

app_name = "prescriptions"

urlpatterns = [
    # ------------------ داشبورد آماری ------------------
    # [GET] - نمایش داشبورد آماری نسخه‌ها
    path("dashboard/", views.prescriptions_dashboard_view, name="prescriptions_dashboard"),

    # ------------------ مدیریت نسخه‌ها ------------------

    # [GET] - نمایش لیست تمام نسخه‌ها (آرشیو)
    path("", views.PrescriptionListView.as_view(), name="prescription_list"), # Changed to class-based view and name

    # [GET, POST] - ایجاد یک نسخه جدید برای یک بیمار مشخص
    # این URL می‌تواند از patient_id یا service_id استفاده کند
    path("create/for-patient/<int:patient_id>/", views.PrescriptionCreateView.as_view(), name="prescription_create_for_patient"),
    path("create/for-service/<int:service_id>/", views.PrescriptionCreateView.as_view(), name="prescription_create_for_service"),


    # [GET] - مشاهده جزئیات یک نسخه خاص با استفاده از شناسه آن (pk)
    path("<int:pk>/", views.PrescriptionDetailView.as_view(), name="prescription_detail"),

    # [GET, POST] - ویرایش یک نسخه خاص
    path("<int:pk>/update/", views.PrescriptionUpdateView.as_view(), name="prescription_update"),

    # [POST] - حذف یک نسخه خاص
    path("<int:pk>/delete/", views.PrescriptionDeleteView.as_view(), name="prescription_delete"),
]