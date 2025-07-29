from django.urls import path

from . import views

app_name = 'appointments'

urlpatterns = [
    # ------------------ نمای اصلی صفحه (Page View) ------------------
    path('calendar/', views.AppointmentCalendarView.as_view(), name='appointment_calendar'),
    path('calendar-jalali/', views.JalaliMonthCalendarView.as_view(), name='calendar_jalali'),

    # ------------------ API برای FullCalendar ------------------
    path('api/events/', views.AppointmentEventListAPIView.as_view(), name='api_events_list'),

    # [POST, PATCH, DELETE] - عملیات CRUD روی نوبت با ویوی واحد
    path('api/appointments/', views.AppointmentCUDAPIView.as_view(), name='api_appointment_create'),  # POST بدون pk
    path('api/appointments/<int:pk>/', views.AppointmentCUDAPIView.as_view(), name='api_appointment_update_delete'),
    # PATCH, DELETE

    # [GET] - بررسی ظرفیت و زمان‌های خالی پزشک
    path('api/availabilities/', views.AvailabilityAPIView.as_view(), name='api_availabilities'),

    # ------------------ جستجوی Select2 ------------------
    path('api/search/patients/', views.PatientSearchAPIView.as_view(), name='api_search_patients'),
    path('api/search/doctors/', views.DoctorSearchAPIView.as_view(), name='api_search_doctors'),
    path('api/search/services/', views.ServiceTypeSearchAPIView.as_view(), name='api_search_services'),
    path('api/search/locations/', views.LocationSearchAPIView.as_view(), name='api_search_locations'),
]
