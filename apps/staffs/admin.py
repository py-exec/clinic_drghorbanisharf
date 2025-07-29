# from django.contrib import admin
# from simple_history.admin import SimpleHistoryAdmin
#
# from .models import (
#     StaffPosition,
#     Staff,
#     AttendanceRecord,
#     LeaveRequest,
#     ShiftAssignment,
#     DailyWorkLog
# )
#
#
# @admin.register(StaffPosition)
# class StaffPositionAdmin(admin.ModelAdmin):
#     list_display = ["title", "created_at"]
#     search_fields = ["title"]
#
#
# @admin.register(Staff)
# class StaffAdmin(SimpleHistoryAdmin):
#     list_display = ["user", "position", "contract_number", "is_active", "created_at"]
#     list_filter = ["is_active", "position"]
#     search_fields = ["user__first_name", "user__last_name", "contract_number"]
#     autocomplete_fields = ["user", "position", "created_by"]
#     readonly_fields = ["created_at", "updated_at"]
#
#
# @admin.register(AttendanceRecord)
# class AttendanceRecordAdmin(admin.ModelAdmin):
#     list_display = ["staff", "date", "clock_in", "clock_out", "method"]
#     list_filter = ["method", "date"]
#     search_fields = ["staff__user__first_name", "staff__user__last_name"]
#     autocomplete_fields = ["staff"]
#
#
# @admin.register(LeaveRequest)
# class LeaveRequestAdmin(admin.ModelAdmin):
#     list_display = ["staff", "leave_type", "start_date", "end_date", "status"]
#     list_filter = ["leave_type", "status"]
#     search_fields = ["staff__user__first_name", "staff__user__last_name", "reason"]
#     autocomplete_fields = ["staff", "reviewed_by"]
#     readonly_fields = ["requested_at", "reviewed_at"]
#
#
# @admin.register(ShiftAssignment)
# class ShiftAssignmentAdmin(admin.ModelAdmin):
#     list_display = ["staff", "shift", "assigned_at"]
#     autocomplete_fields = ["staff", "shift", "assigned_by"]
#     readonly_fields = ["assigned_at"]
#
#
# @admin.register(DailyWorkLog)
# class DailyWorkLogAdmin(admin.ModelAdmin):
#     list_display = ["staff", "date", "shift", "is_late", "left_early", "overtime_hours"]
#     list_filter = ["is_late", "left_early"]
#     search_fields = ["staff__user__first_name", "staff__user__last_name"]
#     autocomplete_fields = ["staff", "shift", "confirmed_by"]
