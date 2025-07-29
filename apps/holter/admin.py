from django.contrib import admin
from .models import (
    HolterDevice,
    HolterStatusLog,
    HolterAssignment,
    HolterInstallation,
    HolterRepairLog,
)


@admin.register(HolterDevice)
class HolterDeviceAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "model_name", "device_type", "status", "is_active", "created_at")
    list_filter = ("status", "device_type", "is_active", "created_at")
    search_fields = ("serial_number", "model_name", "asset_code", "internal_code")
    readonly_fields = ("created_at", "status_updated_at")
    ordering = ("-created_at",)


@admin.register(HolterStatusLog)
class HolterStatusLogAdmin(admin.ModelAdmin):
    list_display = ("device", "old_status", "new_status", "changed_by", "changed_at")
    list_filter = ("old_status", "new_status", "changed_at")
    search_fields = ("device__serial_number", "changed_by__username")


@admin.register(HolterAssignment)
class HolterAssignmentAdmin(admin.ModelAdmin):
    list_display = ("device", "patient", "assigned_at", "returned_at")
    list_filter = ("assigned_at", "returned_at")
    search_fields = ("device__serial_number", "patient__first_name", "patient__last_name")


@admin.register(HolterInstallation)
class HolterInstallationAdmin(admin.ModelAdmin):
    list_display = ("device", "patient", "install_datetime", "technician_name")
    list_filter = ("install_datetime", "technician_name")
    search_fields = ("device__serial_number", "patient__first_name", "patient__last_name", "technician_name")


@admin.register(HolterRepairLog)
class HolterRepairLogAdmin(admin.ModelAdmin):
    list_display = ("device", "repair_start", "repair_end", "repaired_by", "cost")
    list_filter = ("repair_start", "repair_end")
    search_fields = ("device__serial_number", "repaired_by")
    readonly_fields = ("created_at",)