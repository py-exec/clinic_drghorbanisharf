from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    """
    سریالایزر جامع برای مدل Appointment.
    """
    # نمایش اطلاعات خوانا از روابط (اختیاری اما بسیار مفید)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)

    class Meta:
        model = Appointment
        # تمام فیلدهایی که می‌خواهیم از طریق API قابل دسترس باشند
        fields = [
            'id',
            'patient',
            'doctor',
            'service_type',
            'location',
            'resources',
            'date',
            'time',
            'end_time',
            'status',
            'patient_notes',
            'internal_notes',
            # فیلدهای خوانا
            'patient_name',
            'doctor_name',
        ]
        # فیلدهایی که فقط خواندنی هستند و در درخواست‌های POST/PUT نمی‌آیند
        read_only_fields = ['id', 'end_time', 'patient_name', 'doctor_name']

    def validate_date(self, value):  # 👈 اصلاح نام متد به validate_date
        """
        بررسی می‌کند که تاریخ نوبت در گذشته نباشد.
        """
        import datetime  # ایمپورت کتابخانه
        if value < datetime.date.today():
            raise serializers.ValidationError("تاریخ نوبت نمی‌تواند در گذشته باشد.")
        return value
