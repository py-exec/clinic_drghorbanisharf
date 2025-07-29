# apps/staffs/urls.py

from django.urls import path

from . import views

app_name = "staffs"

urlpatterns = [
    # ------------------ مدیریت پرسنل (Staff Members) ------------------
    # URL اصلی منو: 'staffs:staff-list'
    # مسیرها به صورت خودکار با پیشوند /staff/ از فایل اصلی ترکیب می‌شوند.
    path("", views.StaffListView.as_view(), name="staff-list"),
    path("create/", views.StaffCreateView.as_view(), name="staff-create"),
    path("<int:pk>/", views.StaffDetailView.as_view(), name="staff-detail"),
    path("<int:pk>/update/", views.StaffUpdateView.as_view(), name="staff-update"),
    path("<int:pk>/delete/", views.StaffDeleteView.as_view(), name="staff-delete"),

    # ------------------ موقعیت‌های شغلی (Positions) ------------------
    path("positions/", views.StaffPositionListView.as_view(), name="position-list"),
    path("positions/create/", views.StaffPositionCreateView.as_view(), name="position-create"),
    path("positions/<int:pk>/update/", views.StaffPositionUpdateView.as_view(), name="position-update"),
    path("positions/<int:pk>/delete/", views.StaffPositionDeleteView.as_view(), name="position-delete"),

    # ------------------ حضور و غیاب (Attendances) ------------------
    # URL اصلی منو: 'staffs:attendance-list'
    path("attendances/", views.AttendanceRecordListView.as_view(), name="attendance-list"),
    path("attendances/create/", views.AttendanceRecordCreateView.as_view(), name="attendance-create"),
    path("attendances/<int:pk>/update/", views.AttendanceRecordUpdateView.as_view(), name="attendance-update"),
    path("attendances/<int:pk>/delete/", views.AttendanceRecordDeleteView.as_view(), name="attendance-delete"),

    # ------------------ مرخصی‌ها (Leaves) ------------------
    # URL اصلی منو: 'staffs:leave-list'
    path("leaves/", views.LeaveRequestListView.as_view(), name="leave-list"),
    path("leaves/create/", views.LeaveRequestCreateView.as_view(), name="leave-create"),
    path("leaves/<int:pk>/update/", views.LeaveRequestUpdateView.as_view(), name="leave-update"),
    path("leaves/<int:pk>/delete/", views.LeaveRequestDeleteView.as_view(), name="leave-delete"),

    # ------------------ گزارش کار روزانه (Work Logs) ------------------
    path("logs/", views.DailyWorkLogListView.as_view(), name="log-list"),
    path("logs/create/", views.DailyWorkLogCreateView.as_view(), name="log-create"),
    path("logs/<int:pk>/update/", views.DailyWorkLogUpdateView.as_view(), name="log-update"),
    path("logs/<int:pk>/delete/", views.DailyWorkLogDeleteView.as_view(), name="log-delete"),

    # ------------------ گزارشات و جستجو (Reports & Search) ------------------
    # URL اصلی منو (استاتیک): '/staff/report/'
    path("report/excel/", views.staff_report_excel, name="staff-report-excel"),
    path("report/pdf/", views.staff_report_pdf, name="staff-report-pdf"),
    path("search/", views.StaffSearchView.as_view(), name="staff-search"),
]
