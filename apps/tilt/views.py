# apps/tilt/views.py

from apps.appointments.models import Appointment
from apps.reception.models import ReceptionService
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import TiltTestReportForm
from .models import TiltTestReport


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
    """
    ایجاد یک گزارش تست تیلت جدید برای یک خدمت پذیرش شده مشخص.
    """
    reception_service = get_object_or_404(ReceptionService, pk=service_id)

    # بررسی اینکه آیا برای این خدمت قبلا گزارشی ثبت شده
    if TiltTestReport.objects.filter(object_id=service_id).exists():
        messages.warning(request, "برای این خدمت قبلاً گزارش ثبت شده است.")
        return redirect('reception:detail', pk=reception_service.reception.pk)

    if request.method == 'POST':
        form = TiltTestReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.reception_service = reception_service
            report.created_by = request.user
            report.save()
            messages.success(request, "گزارش تست تیلت با موفقیت ایجاد شد.")
            return redirect(report.get_absolute_url())
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
    """
    حذف یک گزارش تست تیلت.
    """
    report = get_object_or_404(TiltTestReport, pk=pk)
    reception_pk = report.reception_service.reception.pk
    if request.method == 'POST':
        report.delete()
        messages.warning(request, "گزارش تست تیلت با موفقیت حذف شد.")
        return redirect('reception:detail', pk=reception_pk)  # بازگشت به صفحه پذیرش

    context = {'report': report}
    return render(request, 'tilt/tilt_confirm_delete.html', context)


# این تابع را به فایل views.py اضافه کنید
@login_required
@permission_required("tilt.view_tilttestreport", raise_exception=True)
def tilt_worklist_view(request):
    today = timezone.now().date()

    from django.db.models import Subquery, OuterRef
    from apps.reception.models import ReceptionServiceStatus

    # Subquery برای آخرین وضعیت
    latest_status_subquery = ReceptionServiceStatus.objects.filter(
        reception_service=OuterRef('pk')  # ✅ درستش کردیم
    ).order_by('-timestamp').values('status')[:1]

    # Annotate با آخرین وضعیت
    services = ReceptionService.objects.annotate(
        latest_status=Subquery(latest_status_subquery)
    ).filter(
        tariff__service_type__code='tilt',
        created_at__date=today
    ).select_related(
        'reception__patient__user',
        'tariff__service_type'
    )

    # آمار: انجام شده‌ها
    done_today_count = services.filter(
        latest_status='done',
        done_at__date=today
    ).count()

    # آمار: صف انتظار (در انتظار یا در حال انجام)
    waiting_list = services.filter(latest_status__in=['pending', 'in_progress']).order_by('created_at')
    in_queue_count = waiting_list.count()

    # آمار: نوبت‌ برنامه‌ریزی شده
    total_scheduled_today_count = Appointment.objects.filter(
        service_type__code='tilt',
        date=today
    ).exclude(status__in=['canceled', 'no_show', 'rejected']).count()

    context = {
        'done_today': done_today_count,
        'in_queue': in_queue_count,
        'total_scheduled': total_scheduled_today_count,
        'waiting_list': waiting_list,
    }

    return render(request, 'tilt/tilt_worklist.html', context)
