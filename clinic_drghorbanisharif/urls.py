# clinic/urls.py (فایل اصلی URL های پروژه)

from apps.accounts.views import dashboard_view
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# توضیح: نام‌های فارسی (verbose_name) برای هر ماژول،
# باید در فایل apps.py مربوط به همان اپلیکیشن تعریف شوند.
# این فایل صرفاً مسئول مسیریابی URL ها است.

urlpatterns = [
    # ------------------ هسته و پنل ادمین ------------------
    path('admin/', admin.site.urls),

    # 🏠 داشبورد (صفحه اصلی)
    # این URL به یک view در اپلیکیشن accounts متصل شده تا داشبورد هر کاربر شخصی‌سازی شود.
    path('', dashboard_view, name='dashboard'),

    # ------------------ ماژول‌های اصلی اپلیکیشن ------------------
    # نکته حیاتی: هر include باید یک namespace داشته باشد که با منوی JSON همخوانی دارد.

    # 👤 بیماران (Patients)
    path("patients/", include("apps.patient.urls", namespace="patient")),

    # ✅ پذیرش (Reception)
    path('reception/', include('apps.reception.urls', namespace='reception')),

    # 🗓 نوبت‌دهی (Appointments)
    # شامل تقویم نوبت‌دهی و API های مربوطه
    path('appointments/', include('apps.appointments.urls', namespace='appointments')),

    # 👨‍⚕️ پزشکان (Doctors)
    path("doctors/", include("apps.doctors.urls", namespace="doctors")),

    # 🩺 خدمات کلینیکی (Clinic Services)
    path("services/ecg/", include("apps.ecg.urls", namespace="ecg")),
    path("services/holter-hr/", include("apps.holter_hr.urls", namespace="holter_hr")),
    path("services/holter-bp/", include("apps.holter_bp.urls", namespace="holter_bp")),  # ✅ اصلاح‌شده
    path("services/procedures/", include("apps.procedures.urls", namespace="procedures")),
    path("services/prescriptions/", include("apps.prescriptions.urls", namespace="prescriptions")),
    path("services/stress/", include("apps.exercise_stress_test.urls", namespace="stress")),
    path("services/tilt/", include("apps.tilt.urls", namespace="tilt")),
    path("services/tte/", include("apps.echo_tte.urls", namespace="tte")),
    path("services/tee/", include("apps.echo_tee.urls", namespace="tee")),

    # 🏷️ انبار و تجهیزات (Inventory & Assets)
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),

    # 🧑‍💼 پرسنل (Staff)
    path("staff/", include("apps.staffs.urls", namespace="staffs")),

    # 🧾 حسابداری (Accounting)
    # این ماژول در منوی JSON وجود داشت و برای عملکرد صحیح منو ضروری است.
    path("accounting/", include("apps.accounting.urls", namespace="accounting")),

    # 👥 کاربران و دسترسی‌ها (Users & Permissions)
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("backup/", include("apps.backup.urls", namespace="backup")),
    # ------------------ ماژول‌های اضافی (خارج از منوی اولیه) ------------------
    # این ماژول در فایل شما بود اما در منوی JSON اولیه تعریف نشده بود.
    # در صورت نیاز می‌توانیم بعداً آن را به منو اضافه کنیم.
    path("clinic-messenger/", include("apps.clinic_messenger.urls", namespace="clinic_messenger")),
]

# ------------------ مدیریت خطاهای سفارشی ------------------
# این خطوط موقتا کامنت شده‌اند تا از بروز خطا قبل از ساخت view ها جلوگیری شود.
# handler403 = "clinic.views.custom_permission_denied_view"
# handler404 = "clinic.views.custom_page_not_found_view"
# handler500 = "clinic.views.custom_server_error_view"

# ------------------ سرویس‌دهی فایل‌های مدیا در حالت توسعه ------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
