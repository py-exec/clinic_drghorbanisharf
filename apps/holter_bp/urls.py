from django.urls import path

from . import views

app_name = "holter_bp"

urlpatterns = [
    # ------------------ داشبورد کاری و لیست‌ها ------------------
    path("worklist/", views.holter_bp_worklist_view, name="holter_bp_worklist"),
    path("archive/", views.holter_bp_archive_view, name="holter_bp_archive"),

    # ------------------ مدیریت یک گزارش کامل هلتر ------------------
    path("<int:pk>/", views.HolterBPDetailView.as_view(), name="holter_bp_detail"),

    # ------------------ مراحل فرآیند هلتر ------------------
    # مرحله ۱: نصب دستگاه
    path("install/for-service/<int:service_id>/", views.HolterBPInstallationCreateView.as_view(),
         name="holter_bp_install_create"),
    path("install/<int:pk>/update/", views.HolterBPInstallationUpdateView.as_view(), name="holter_bp_install_update"),

    # مرحله ۲: دریافت دستگاه از بیمار
    path("installation/<int:installation_pk>/return/", views.HolterBPReceptionCreateView.as_view(),
         name="holter_bp_reception_create"),
    path("return/<int:pk>/update/", views.HolterBPReceptionUpdateView.as_view(), name="holter_bp_reception_update"),

    # مرحله ۳: خوانش و تحلیل گزارش
    path("installation/<int:installation_pk>/read/", views.HolterBPReadingCreateView.as_view(),
         name="holter_bp_reading_create"),
    path("reading/<int:pk>/update/", views.HolterBPReadingUpdateView.as_view(), name="holter_bp_reading_update"),

    # ------------------ حذف فرآیند ------------------
    path("<int:pk>/delete/", views.HolterBPDeleteView.as_view(), name="holter_bp_delete"),
]
