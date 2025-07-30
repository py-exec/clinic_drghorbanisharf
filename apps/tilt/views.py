# apps/tilt/views.py


from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import TiltTestReportForm
from .models import TiltTestReport
from apps.reception.models import ServiceType
from django.db.models import Subquery, OuterRef
from django.http import JsonResponse
from apps.reception.models import ReceptionService, ReceptionServiceStatus
from apps.appointments.models import Appointment
import logging

logger = logging.getLogger(__name__)


@login_required
@permission_required("tilt.view_tilttestreport", raise_exception=True)
def tilt_test_list(request):
    """
    نمایش لیست تمام گزارش‌های تست تیلت با قابلیت صفحه‌بندی.
    """
    report_list = TiltTestReport.objects.select_related(
        'created_by', 'prescription'
    ).order_by('-created_at')

    paginator = Paginator(report_list, 15)  # نمایش ۱۵ آیتم در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'tilt/tilt_list.html', context)


@login_required
@permission_required("tilt.view_tilttestreport", raise_exception=True)
def tilt_test_detail(request, pk):
    """
    نمایش جزئیات یک گزارش تست تیلت.
    """
    report = get_object_or_404(TiltTestReport, pk=pk)
    context = {'report': report}
    return render(request, 'tilt/tilt_detail.html', context)


@login_required
@permission_required("tilt.add_tilttestreport", raise_exception=True)
def tilt_create_view(request, service_id):
    reception_service = get_object_or_404(ReceptionService, pk=service_id)

    # اگر قبلاً گزارشی وجود داشته باشه
    if TiltTestReport.objects.filter(object_id=service_id).exists():
        messages.warning(request, "برای این خدمت قبلاً گزارش ثبت شده است.")
        existing_report = TiltTestReport.objects.get(object_id=service_id)
        return redirect(existing_report.get_absolute_url())

    if request.method == 'POST':
        form = TiltTestReportForm(request.POST, request.FILES)
        for field, errors in form.errors.items():
            print(f"{field}: {errors}")

        if form.is_valid():
            report = form.save(commit=False)
            report.content_object = reception_service  # ست‌کردن GenericForeignKey
            report.patient = reception_service.reception.patient  # مقدار دادن patient
            report.created_by = request.user
            report.save()
            messages.success(request, "گزارش تست تیلت با موفقیت ایجاد شد.")
            return redirect(report.get_absolute_url())
        else:
            messages.error(request, "خطا در ثبت فرم. لطفاً ورودی‌ها را بررسی کنید.")
    else:
        form = TiltTestReportForm()

    context = {
        'form': form,
        'service': reception_service,
        'patient': reception_service.reception.patient
    }
    return render(request, 'tilt/tilt_form.html', context)


@login_required
@permission_required("tilt.change_tilttestreport", raise_exception=True)
def tilt_test_update(request, pk):
    """
    ویرایش یک گزارش تست تیلت موجود.
    """
    report = get_object_or_404(TiltTestReport, pk=pk)
    if request.method == 'POST':
        form = TiltTestReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "گزارش تست تیلت با موفقیت ویرایش شد.")
            return redirect(report.get_absolute_url())
    else:
        form = TiltTestReportForm(instance=report)

    context = {
        'form': form,
        'report': report,
        'patient': report.patient
    }
    return render(request, 'tilt/tilt_form.html', context)


@login_required
@permission_required("tilt.delete_tilttestreport", raise_exception=True)
def tilt_test_delete(request, pk):
    report = get_object_or_404(TiltTestReport, pk=pk)

    # ← تغییر مهم: استفاده از content_object
    reception_service = report.content_object  # فرض بر اینه که همیشه از نوع ReceptionService هست
    reception_pk = reception_service.reception.pk  # یا هر فیلد مشابهی که در مدل ReceptionService هست

    if request.method == 'POST':
        report.delete()
        messages.warning(request, "گزارش تست تیلت با موفقیت حذف شد.")
        return redirect('tilt:tilt_report_archive')

    context = {
        'report': report,
        'patient': report.content_object.patient if hasattr(report.content_object, "patient") else None,
        'created_at': report.created_at,
        'final_result': report.final_result if hasattr(report, "final_result") else "-"
    }

    return render(request, 'tilt/tilt_confirm_delete.html', context)


@login_required
@permission_required("tilt.view_tilttestreport", raise_exception=True)
def tilt_worklist_view(request):
    today = timezone.localdate()
    model_path = 'apps.tilt.models.TiltTestReport'

    # پیدا کردن تمام service type هایی که به مدل تیلت وصل هستند
    tilt_service_types = ServiceType.objects.filter(model_path=model_path)
    tilt_type_codes = list(tilt_service_types.values_list('code', flat=True))
    logger.info(f"✅ tilt_service_types codes: {tilt_type_codes}")

    # ساخت ساب‌کوئری برای گرفتن آخرین وضعیت
    latest_status_subquery = ReceptionServiceStatus.objects.filter(
        reception_service=OuterRef('pk')
    ).order_by('-timestamp').values('status')[:1]

    # فیلتر خدمات امروز که مدلشان تیلت است
    services = ReceptionService.objects.filter(
        tariff__service_type__in=tilt_service_types,
        created_at__date=today
    ).annotate(
        latest_status_value=Subquery(latest_status_subquery)
    ).select_related('reception__patient')

    logger.info(f"🔎 Total services found: {services.count()}")

    # لاگ گرفتن از وضعیت تمام رکوردها
    logger.info("🧪 All services with their latest_status_value:")
    for s in services:
        logger.info(
            f"→ Service ID: {s.id} | Patient: {s.reception.patient.full_name} | Status: {s.latest_status_value}")

    # آمار انجام شده‌ها
    done_today_count = services.filter(
        latest_status_value='done',
        done_at__date=today
    ).count()
    logger.info(f"✅ Done today count: {done_today_count}")

    # لیست صف انتظار (pending یا in_progress)
    waiting_list = services.filter(
        latest_status_value__in=['pending', 'in_progress']
    ).order_by('created_at')

    in_queue_count = waiting_list.count()
    logger.info(f"🕒 In queue count: {in_queue_count}")
    logger.info(f"📋 Waiting List IDs: {[s.id for s in waiting_list]}")

    # آمار نوبت‌های برنامه‌ریزی‌شده
    total_scheduled_today_count = Appointment.objects.filter(
        service_type__in=tilt_service_types,
        date=today
    ).exclude(status__in=['canceled', 'no_show', 'rejected']).count()
    logger.info(f"📅 Total scheduled today: {total_scheduled_today_count}")

    context = {
        'done_today': done_today_count,
        'in_queue': in_queue_count,
        'total_scheduled': total_scheduled_today_count,
        'waiting_list': waiting_list,
    }

    return render(request, 'tilt/tilt_worklist.html', context)


@login_required
def tilt_dashboard_stats(request):
    today = timezone.localdate()
    model_path = 'apps.tilt.models.TiltTestReport'
    tilt_service_types = ServiceType.objects.filter(model_path=model_path)

    latest_status_subquery = ReceptionServiceStatus.objects.filter(
        reception_service=OuterRef('pk')
    ).order_by('-timestamp').values('status')[:1]

    services = ReceptionService.objects.filter(
        tariff__service_type__in=tilt_service_types,
        created_at__date=today
    ).annotate(
        latest_status_value=Subquery(latest_status_subquery)
    )

    done_today_count = services.filter(
        latest_status_value='done',
        done_at__date=today
    ).count()

    in_queue_count = services.filter(
        latest_status_value__in=['pending', 'in_progress']
    ).count()

    total_scheduled_today_count = Appointment.objects.filter(
        service_type__in=tilt_service_types,
        date=today
    ).exclude(status__in=['canceled', 'no_show', 'rejected']).count()

    return JsonResponse({
        'done_today': done_today_count,
        'in_queue': in_queue_count,
        'total_scheduled': total_scheduled_today_count,
    })
