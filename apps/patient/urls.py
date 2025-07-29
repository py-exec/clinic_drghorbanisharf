# apps/patient/urls.py

from django.urls import path

from . import views

app_name = "patient"

urlpatterns = [
    # --- جستجو و ثبت بیمار (فرم یکپارچه) ---
    path("lookup/", views.patient_lookup_view, name="patient_lookup"),

    # ثبت نهایی بیمار (بعد از جستجو)
    path("register/", views.patient_create_view, name="patient_create"),

    # --- مدیریت بیماران (CRUD) ---
    path("", views.patient_list_view, name="patient_list"),
    path("<int:pk>/", views.patient_detail_view, name="patient_detail"),
    path("<int:pk>/update/", views.patient_update_view, name="patient_update"),
    path("<int:pk>/delete/", views.patient_delete_view, name="patient_delete"),

    # --- API ---
    path("api/search/", views.search_patients_api, name="api_search_patients"),
]
