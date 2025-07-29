# apps/reception/urls.py

from django.urls import path

from . import views

app_name = "reception"

urlpatterns = [
    # ------------------ مدیریت پذیرش (Reception CRUD) ------------------
    # مسیرها به صورت خودکار با پیشوند /reception/ از فایل اصلی ترکیب می‌شوند.

    # [GET] - نمایش لیست پذیرش‌ها
    path("", views.ReceptionListView.as_view(), name="list"),

    # [GET, POST] - ثبت پذیرش جدید
    path("start/", views.ReceptionStartView.as_view(), name="start"),
    path("create/<int:patient_id>/", views.ReceptionCreateView.as_view(), name="create"),

    # [GET] - مشاهده جزئیات یک پذیرش
    path("<int:pk>/", views.ReceptionDetailView.as_view(), name="detail"),

    # [GET, POST] - ویرایش یک پذیرش
    path("<int:pk>/update/", views.ReceptionUpdateView.as_view(), name="update"),

    # [POST] - حذف یک پذیرش
    path("<int:pk>/delete/", views.ReceptionDeleteView.as_view(), name="delete"),

    # ------------------ مدیریت خدمات (ServiceType) ------------------
    path("services/", views.ServiceTypeListView.as_view(), name="service_list"),
    path("services/create/", views.ServiceTypeCreateView.as_view(), name="service_create"),
    path("services/<int:pk>/update/", views.ServiceTypeUpdateView.as_view(), name="service_update"),
    path("services/<int:pk>/delete/", views.ServiceTypeDeleteView.as_view(), name="service_delete"),

    # ------------------ مدیریت تعرفه‌ها (ServiceTariff) ------------------
    path("tariffs/", views.ServiceTariffListView.as_view(), name="tariff_list"),
    path("tariffs/create/", views.ServiceTariffCreateView.as_view(), name="tariff_create"),
    path("tariffs/<int:pk>/update/", views.ServiceTariffUpdateView.as_view(), name="tariff_update"),
    path("tariffs/<int:pk>/delete/", views.ServiceTariffDeleteView.as_view(), name="tariff_delete"),

    # ------------------ مدیریت خدمات در پذیرش (Service Management) ------------------
    path("<int:pk>/add-service/", views.add_service_to_reception, name="add_service"),
    path("services/<int:service_id>/mark-done/", views.mark_service_done, name="mark_service_done"),
    path("services/<int:service_id>/cancel/", views.cancel_service, name="cancel_service"),

    # ------------------ عملیات مالی (Financial Operations) ------------------
    path("<int:pk>/confirm-payment/", views.confirm_payment, name="confirm_payment"),

    # ------------------ API و Partial Views ------------------
    path("api/get-service-cost/", views.get_service_cost_api, name="api_get_service_cost"),
    path("api/<int:pk>/services/", views.reception_services_api, name="api_reception_services"),
    path("partial/table/", views.reception_table_partial, name="reception_table_partial"),
    path("api/<int:service_id>/change-status/", views.ChangeReceptionServiceStatusAPIView.as_view(), name="change-service-status"),
]

