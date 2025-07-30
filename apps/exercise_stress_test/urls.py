# apps/exercise_stress_test/urls.py

from django.urls import path

from . import views

app_name = "exercise_stress_test"

urlpatterns = [
    # ------------------ داشبورد کاری (Worklist) ------------------
    # [GET] - نمایش داشبورد کاری تست ورزش / استرس اکو
    path("worklist/", views.stress_test_worklist_view, name="stress_test_worklist"),

    # ------------------ لیست و مدیریت گزارش‌های تست ورزش ------------------

    # [GET] - نمایش لیست تمام گزارش‌های تست ورزش (آرشیو)
    path("archive/", views.StressTestReportListView.as_view(), name="stress_list"), # Changed to class-based view

    # [GET, POST] - ایجاد یک گزارش تست ورزش جدید برای یک خدمت پذیرش مشخص
    # استفاده از service_id برای اتصال به ReceptionService
    path("create/for-service/<int:service_id>/", views.StressTestReportCreateView.as_view(), name="stress_create"),

    # [GET] - مشاهده جزئیات یک گزارش تست ورزش خاص با استفاده از شناسه گزارش (pk)
    path("<int:pk>/", views.StressTestReportDetailView.as_view(), name="stress_detail"),

    # [GET, POST] - ویرایش یک گزارش تست ورزش خاص
    path("<int:pk>/update/", views.StressTestReportUpdateView.as_view(), name="stress_update"),

    # [POST] - حذف یک گزارش تست ورزش خاص
    path("<int:pk>/delete/", views.StressTestReportDeleteView.as_view(), name="stress_delete"),
]