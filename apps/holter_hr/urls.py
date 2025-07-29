from django.urls import path

from . import views

app_name = "holter_hr"

urlpatterns = [
    path("worklist/", views.holter_hr_worklist_view, name="holter_hr_worklist"),
    path("archive/", views.holter_hr_archive_view, name="holter_hr_archive"),

    path("<int:pk>/", views.HolterHRDetailView.as_view(), name="holter_hr_detail"),
    path("<int:pk>/delete/", views.HolterHRDeleteView.as_view(), name="holter_hr_delete"),

    path("install/for-service/<int:service_id>/", views.HolterHRInstallationCreateView.as_view(),
         name="holter_hr_install_create"),
    path("install/<int:pk>/update/", views.HolterHRInstallationUpdateView.as_view(), name="holter_hr_install_update"),

    path("installation/<int:installation_pk>/return/", views.HolterHRReceptionCreateView.as_view(),
         name="holter_hr_reception_create"),
    path("return/<int:pk>/update/", views.HolterHRReceptionUpdateView.as_view(), name="holter_hr_reception_update"),

    path("installation/<int:installation_pk>/read/", views.HolterHRReadingCreateView.as_view(),
         name="holter_hr_reading_create"),
    path("reading/<int:pk>/update/", views.HolterHRReadingUpdateView.as_view(), name="holter_hr_reading_update"),
]
