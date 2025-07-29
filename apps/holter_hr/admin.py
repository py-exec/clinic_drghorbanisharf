# apps/holter_hr/admin.py

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import HolterHRInstallation, HolterHRReception, HolterHRReading


@admin.register(HolterHRInstallation)
class HolterHRInstallationAdmin(SimpleHistoryAdmin):
    list_display = ['tracking_code', 'patient', 'install_datetime', 'device', 'technician']
    list_filter = ['install_datetime', 'technician']
    search_fields = ['tracking_code', 'patient__user__first_name', 'patient__user__last_name']


@admin.register(HolterHRReception)
class HolterHRReceptionAdmin(SimpleHistoryAdmin):
    list_display = ['installation', 'receive_datetime', 'received_by']
    list_filter = ['receive_datetime', 'received_by']
    search_fields = ['installation__tracking_code', 'installation__patient__user__first_name']


@admin.register(HolterHRReading)
class HolterHRReadingAdmin(SimpleHistoryAdmin):
    list_display = ['installation', 'read_datetime', 'interpreted_by', 'avg_heart_rate']
    list_filter = ['read_datetime', 'interpreted_by']
    search_fields = ['installation__tracking_code', 'installation__patient__user__first_name']
