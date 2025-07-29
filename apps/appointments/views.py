# apps/appointments/views.py

import datetime
from apps.accounts.models import User
from apps.doctors.models import Doctor
from apps.patient.models import Patient
from apps.reception.models import Location, ServiceType
from datetime import date, time, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import render
from django.views import View
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import status
# ایمپورت تمام مدل‌های مورد نیاز
from .models import Appointment
from .serializers import AppointmentSerializer


# ====================================================================
#  ۱. نمای اصلی تقویم (HTML) - بدون تغییر
# ====================================================================
class AppointmentCalendarView(View):
    """
    نمای HTML برای نمایش تقویم نوبت‌ها.
    این ویو داده‌های اولیه برای فیلترهای سایدبار را به قالب ارسال می‌کند.
    """
    template_name = 'appointments/calendar.html'

    def get(self, request, *args, **kwargs):
        all_doctors = Doctor.objects.filter(is_active=True).select_related('user')
        all_locations = Location.objects.filter(is_active=True)
        context = {
            'all_doctors': all_doctors,
            'all_locations': all_locations,
        }
        return render(request, self.template_name, context)


# ====================================================================
#  ۲. API برای دریافت لیست نوبت‌ها (برای FullCalendar) - بروز شده
# ====================================================================
class AppointmentEventListAPIView(APIView):
    """
    API برای دریافت لیست نوبت‌ها جهت نمایش در FullCalendar.
    خروجی این API کاملاً برای FullCalendar بهینه شده است (شامل رنگ‌بندی و اطلاعات کامل در extendedProps).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_str = request.query_params.get('start', '').split('T')[0]
        end_str = request.query_params.get('end', '').split('T')[0]
        doctor_id = request.query_params.get('doctor_id')
        location_id = request.query_params.get('location_id')
        status_filter = request.query_params.get('status')

        queryset = Appointment.objects.all().select_related(
            'patient__user', 'doctor__user', 'service_type', 'location'
        ).prefetch_related('resources')

        if start_str and end_str:
            queryset = queryset.filter(date__range=[start_str, end_str])
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        STATUS_COLORS = {
            'pending': {'backgroundColor': '#ff9f43', 'borderColor': '#ff9f43'},
            'booked': {'backgroundColor': '#7367f0', 'borderColor': '#7367f0'},
            'confirmed': {'backgroundColor': '#00cfe8', 'borderColor': '#00cfe8'},
            'check_in': {'backgroundColor': '#8e44ad', 'borderColor': '#8e44ad'},
            'in_progress': {'backgroundColor': '#3498db', 'borderColor': '#3498db'},
            'completed': {'backgroundColor': '#28c76f', 'borderColor': '#28c76f'},
            'canceled': {'backgroundColor': '#a8a8a8', 'borderColor': '#a8a8a8'},
            'no_show': {'backgroundColor': '#ea5455', 'borderColor': '#ea5455'},
        }

        events = []
        for app in queryset:
            color = STATUS_COLORS.get(app.status, {'backgroundColor': '#6e6e6e', 'borderColor': '#6e6e6e'})
            events.append({
                'id': app.id,
                'title': app.calendar_title,
                'start': app.get_full_start_datetime,
                'end': app.get_full_end_datetime,
                'allDay': False,
                'backgroundColor': color['backgroundColor'],
                'borderColor': color['borderColor'],
                'extendedProps': {
                    'patient_id': app.patient.id,
                    'patientName': app.patient_full_name,
                    'doctor_id': app.doctor.id,
                    'doctorName': app.doctor_full_name,
                    'service_type_id': app.service_type.id,
                    'serviceName': app.service_name,
                    'location_id': app.location.id,
                    'locationName': app.location_name,
                    'statusDisplay': app.get_status_display(),
                    'method': app.method,
                    'patient_notes': app.patient_notes or '',
                    'internal_notes': app.internal_notes or '',
                    'resource_ids': list(app.resources.values_list('id', flat=True))
                }
            })
        return Response(events)


# ====================================================================
#  ۳. API برای عملیات CRUD - بروز شده
# ====================================================================
class AppointmentCUDAPIView(APIView):
    """API واحد برای Create, Update, Delete نوبت‌ها."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """ایجاد یک نوبت جدید"""
        data = request.data.copy()
        try:
            start_datetime_str = data.get('start')
            if not start_datetime_str:
                return Response({'status': 'error', 'errors': {'start': ['تاریخ و زمان شروع الزامی است.']}},
                                status=status.HTTP_400_BAD_REQUEST)

            start_datetime = datetime.datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
            data['date'] = start_datetime.date()
            data['time'] = start_datetime.time()
        except (TypeError, ValueError):
            return Response({'status': 'error', 'errors': {'start': ['فرمت تاریخ و زمان نامعتبر است.']}},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AppointmentSerializer(data=data)
        if serializer.is_valid():
            try:
                appointment_instance = serializer.save(created_by=request.user)
                appointment_instance.full_clean()  # 🎯 فراخوانی clean مدل برای بررسی تمام تداخل‌ها
                return Response({'status': 'success', 'message': 'نوبت با موفقیت ثبت شد.'},
                                status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({'status': 'error', 'errors': e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, *args, **kwargs):
        """ویرایش یک نوبت موجود"""
        try:
            appointment = Appointment.objects.get(pk=pk)
        except Appointment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        if 'start' in data:
            start_datetime = datetime.datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
            data['date'] = start_datetime.date()
            data['time'] = start_datetime.time()

        # برای end_time، اگر ارسال شده باشد، آن را هم پردازش می‌کنیم (برای resize)
        if 'end' in data and data['end']:
            end_datetime = datetime.datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
            data['end_time'] = end_datetime.time()

        serializer = AppointmentSerializer(appointment, data=data, partial=True)
        if serializer.is_valid():
            try:
                updated_instance = serializer.save()
                updated_instance.full_clean()
                return Response({'status': 'success', 'message': 'نوبت با موفقیت به‌روزرسانی شد.'})
            except ValidationError as e:
                return Response({'status': 'error', 'errors': e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """لغو کردن یک نوبت (حذف نرم)"""
        try:
            appointment = Appointment.objects.get(pk=pk)
            appointment.cancel(reason='لغو توسط کاربر از طریق تقویم', user=request.user)
            return Response({'status': 'success', 'message': 'نوبت با موفقیت لغو شد.'}, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# ====================================================================
#  ۴. API های جستجو برای Select2 - بروز شده و هوشمند
# ====================================================================

class PatientSearchAPIView(APIView):
    """جستجوی بیمار برای Select2"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        if len(query) < 2: return Response({'results': []})
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) | Q(
                user__national_code__icontains=query))[:20]
        # 🎯 فرض می‌کنیم متد get_full_name_with_code در مدل User شما وجود دارد
        results = [{'id': p.id, 'text': p.user.get_full_name_with_code()} for p in patients]
        return Response({'results': results})


class DoctorSearchAPIView(APIView):
    """جستجوی پزشک. اگر location_id ارسال شود، پزشکان را بر اساس آن فیلتر می‌کند."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        location_id = request.query_params.get('location_id')
        queryset = Doctor.objects.filter(is_active=True)

        # 🎯 هوشمندی: فیلتر پزشکان بر اساس شعبه انتخاب شده
        if location_id:
            queryset = queryset.filter(locations__id=location_id)

        if query:
            queryset = queryset.filter(Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query))

        doctors = queryset.distinct()[:20]
        results = [{'id': d.id, 'text': d.user.get_full_name()} for d in doctors]
        return Response({'results': results})


class ServiceTypeSearchAPIView(APIView):
    """جستجوی خدمات. خروجی شامل مدت زمان خدمت برای استفاده در فرانت‌اند است."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        # 🎯 این بخش می‌تواند در آینده برای فیلتر خدمات بر اساس پزشک استفاده شود
        # doctor_id = request.query_params.get('doctor_id')

        queryset = ServiceType.objects.filter(is_active=True)
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(code__icontains=query))

        services = queryset[:20]
        # 🎯 هوشمندی: ارسال `duration` در پاسخ API
        results = [{'id': s.id, 'text': s.name, 'duration': s.duration_minutes} for s in services]
        return Response({'results': results})


class LocationSearchAPIView(APIView):
    """جستجوی شعبه. اگر doctor_id ارسال شود، فقط شعب محل فعالیت همان پزشک را برمی‌گرداند."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        doctor_id = request.query_params.get('doctor_id')

        # 🎯 هوشمندی: فیلتر شعب بر اساس پزشک انتخاب شده
        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                queryset = doctor.locations.filter(is_active=True)
            except Doctor.DoesNotExist:
                queryset = Location.objects.none()
        else:
            queryset = Location.objects.filter(is_active=True)

        if query:
            queryset = queryset.filter(name__icontains=query)

        locations = queryset.distinct()[:20]
        results = [{'id': loc.id, 'text': loc.name} for loc in locations]
        return Response({'results': results})


class AvailabilityAPIView(APIView):
    """
    API برای یافتن و نمایش زمان‌های *غیرقابل دسترس* یک پزشک در یک شعبه.
    خروجی این ویو به عنوان background-events در FullCalendar استفاده می‌شود.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        doctor_id = request.query_params.get('doctor_id')
        location_id = request.query_params.get('location_id')
        start_str = request.query_params.get('start', '').split('T')[0]
        end_str = request.query_params.get('end', '').split('T')[0]

        if not all([doctor_id, location_id, start_str, end_str]):
            return Response([], status=status.HTTP_200_OK)  # اگر اطلاعات ناقص بود، چیزی برنگردان

        try:
            doctor = Doctor.objects.get(id=doctor_id)
            location = Location.objects.get(id=location_id)
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
        except (Doctor.DoesNotExist, Location.DoesNotExist, ValueError):
            return Response({"error": "پزشک یا شعبه نامعتبر است"}, status=status.HTTP_400_BAD_REQUEST)

        unavailability_events = []

        # پیمایش روز به روز در بازه زمانی درخواست شده
        current_date = start_date
        while current_date <= end_date:
            day_of_week = (current_date.weekday() + 2) % 7  # 0=شنبه, 6=جمعه

            # ۱. پیدا کردن ساعات خارج از شیفت کاری
            schedules = DoctorSchedule.objects.filter(doctor=doctor, location=location, day_of_week=day_of_week,
                                                      is_active=True)

            working_intervals = [(s.start_time, s.end_time) for s in schedules]

            # اگر برای این روز هیچ شیفتی تعریف نشده، کل روز غیرقابل دسترس است
            if not working_intervals:
                unavailability_events.append(self._create_background_event(current_date, time.min, time.max))
            else:
                # محاسبه گپ‌های بین شیفت‌ها و قبل و بعدشان
                working_intervals.sort()
                last_end_time = time.min
                for start_shift, end_shift in working_intervals:
                    if start_shift > last_end_time:
                        unavailability_events.append(
                            self._create_background_event(current_date, last_end_time, start_shift))
                    last_end_time = end_shift
                if last_end_time < time.max:
                    unavailability_events.append(self._create_background_event(current_date, last_end_time, time.max))

            current_date += timedelta(days=1)

        # ۲. اضافه کردن بلاک‌های زمانی (مرخصی/جلسه)
        block_times = BlockTime.objects.filter(
            Q(doctor=doctor) | Q(location=location),
            start_datetime__date__lte=end_date,
            end_datetime__date__gte=start_date
        )
        for block in block_times:
            unavailability_events.append(
                self._create_background_event_from_datetime(block.start_datetime, block.end_datetime, title=block.name))

        return Response(unavailability_events)

    def _create_background_event(self, event_date, start_time, end_time, title="غیرقابل دسترس"):
        """یک رویداد پس‌زمینه برای FullCalendar می‌سازد"""
        return {
            'start': timezone.make_aware(datetime.datetime.combine(event_date, start_time)).isoformat(),
            'end': timezone.make_aware(datetime.datetime.combine(event_date, end_time)).isoformat(),
            'display': 'background',
            'color': '#f2f2f2',  # رنگ خاکستری برای زمان‌های غیرفعال
            'title': title
        }

    def _create_background_event_from_datetime(self, start_dt, end_dt, title):
        return {
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'display': 'background',
            'color': '#ffdede',  # یک رنگ متفاوت برای مرخصی‌ها
            'title': title,
        }


from .calendar_utils import get_jalali_calendar_weeks


class JalaliMonthCalendarView(View):
    template_name = 'appointments/jalali_calendar.html'

    def get(self, request, *args, **kwargs):
        import jdatetime

        year = int(request.GET.get('year', jdatetime.date.today().year))
        month = int(request.GET.get('month', jdatetime.date.today().month))

        weeks = get_jalali_calendar_weeks(year, month)

        # پیمایش
        current = jdatetime.date(year, month, 1)
        prev_month = current - jdatetime.timedelta(days=1)
        next_month = current + jdatetime.timedelta(days=31)

        context = {
            'weeks': weeks,
            'year': year,
            'month': month,
            'prev_year': prev_month.year,
            'prev_month': prev_month.month,
            'next_year': next_month.year,
            'next_month': next_month.month,
        }
        return render(request, self.template_name, context)
