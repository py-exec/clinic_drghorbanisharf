import jdatetime
from datetime import timedelta

from .models import Appointment


def get_jalali_calendar_weeks(year, month):
    days = []

    # روز اول ماه شمسی
    j_start = jdatetime.date(year, month, 1)
    start_weekday = j_start.weekday()  # 0=شنبه، 6=جمعه

    # پر کردن روزهای خالی قبل از روز اول
    for _ in range(start_weekday):
        days.append(None)

    # پر کردن روزهای واقعی ماه
    for day in range(1, 32):
        try:
            j_date = jdatetime.date(year, month, day)
            g_date = j_date.togregorian()
            appointments = Appointment.objects.filter(date=g_date)
            days.append({
                'jdate': j_date,
                'gdate': g_date,
                'weekday': j_date.weekday(),
                'appointments': appointments
            })
        except ValueError:
            break  # پایان ماه

    # پر کردن روزهای خالی بعد از آخرین روز برای تکمیل ردیف
    while len(days) % 7 != 0:
        days.append(None)

    # تقسیم کل لیست به هفته‌ها (لیست‌های ۷تایی)
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    return weeks
