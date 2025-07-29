from django.urls import path
from . import views

app_name = "holter"

urlpatterns = [
    # ==== ثبت و ساخت دستگاه ====
    path("create/", views.holter_create, name="holter-create"),

    # ==== فرم‌های نصب و تحویل ====
    path("install/<int:patient_id>/", views.holter_installation_form, name="holter-installation"),
    path("receive/<int:patient_id>/", views.holter_receive_form, name="holter-receive"),

    # ==== لیست‌ها ====
    path("list/", views.holter_list, name="holter-device-list"),  # لیست کلی هولتر
    # path("installations/", views.holter_installation_list, name="holter-installation-list"),  # لیست نصب‌شده‌ها
    # path("receives/", views.holter_receive_list, name="holter-receive-list"),  # لیست دریافت‌شده‌ها

    # ==== جزئیات و عملیات ====
    path("<int:pk>/", views.holter_detail, name="holter-detail"),
    path("<int:pk>/change-status/", views.holter_change_status, name="holter-change-status"),
    path("<int:pk>/delete/", views.holter_delete, name="holter-delete"),
]