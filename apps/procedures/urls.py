# apps/procedures/urls.py

from django.urls import path

from . import views

app_name = "procedures"

urlpatterns = [
    # ------------------ مدیریت پروسیجرها (Procedures) ------------------

    # [GET] - نمایش لیست تمام پروسیجرها
    # URL اصلی منو: 'procedures:procedure-list'
    path("", views.procedure_list, name="procedure-list"),

    # [GET, POST] - ایجاد یک پروسیجر جدید برای یک بیمار مشخص
    path("create/for-patient/<int:patient_id>/", views.procedure_create, name="procedure-create"),

    # [GET] - مشاهده جزئیات یک پروسیجر خاص با استفاده از شناسه آن (pk)
    path("<int:pk>/", views.procedure_detail, name="procedure-detail"),

    # [GET, POST] - ویرایش یک پروسیجر خاص
    path("<int:pk>/update/", views.procedure_update, name="procedure-update"),

    # [POST] - حذف یک پروسیجر خاص
    path("<int:pk>/delete/", views.procedure_delete, name="procedure-delete"),
]
