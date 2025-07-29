# apps/doctors/urls.py

from django.urls import path

from . import views

app_name = "doctors"

urlpatterns = [
    # ------------------ مدیریت پزشکان (Doctors) ------------------
    # URL اصلی منو: 'doctors:doctor-list'
    # مسیرها به صورت خودکار با پیشوند /doctors/ از فایل اصلی ترکیب می‌شوند.
    path("", views.DoctorListView.as_view(), name="doctor-list"),
    path("create/", views.DoctorCreateView.as_view(), name="doctor-create"),
    path("<int:pk>/", views.DoctorDetailView.as_view(), name="doctor-detail"),
    path("<int:pk>/update/", views.DoctorUpdateView.as_view(), name="doctor-update"),
    path("<int:pk>/delete/", views.DoctorDeleteView.as_view(), name="doctor-delete"),

    # ------------------ مدیریت تخصص‌ها (Specialties) ------------------
    # URL اصلی منو: 'doctors:specialty-list'
    path("specialties/", views.SpecialtyListView.as_view(), name="specialty-list"),
    path("specialties/create/", views.SpecialtyCreateView.as_view(), name="specialty-create"),
    path("specialties/<int:pk>/update/", views.SpecialtyUpdateView.as_view(), name="specialty-update"),
    path("specialties/<int:pk>/delete/", views.SpecialtyDeleteView.as_view(), name="specialty-delete"),

    # ------------------ دسته‌بندی تخصص‌ها (Specialty Categories) ------------------
    # این بخش در منوی اولیه نیست اما برای مدیریت سیستم لازم است.
    path("specialty-categories/", views.SpecialtyCategoryListView.as_view(), name="specialty-category-list"),
    path("specialty-categories/create/", views.SpecialtyCategoryCreateView.as_view(), name="specialty-category-create"),
    path("specialty-categories/<int:pk>/update/", views.SpecialtyCategoryUpdateView.as_view(),
         name="specialty-category-update"),
    path("specialty-categories/<int:pk>/delete/", views.SpecialtyCategoryDeleteView.as_view(),
         name="specialty-category-delete"),
]
