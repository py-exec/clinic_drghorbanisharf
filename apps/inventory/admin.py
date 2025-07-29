from django.contrib import admin
from .models import (
    Partner, Item, Inventory, StockIn, StockInItem, StockOut, StockOutItem,
    Loan, PatientUsageLog, MaintenanceLog, CalibrationLog, DecommissionLog,
    ItemStatusHistory, DocumentAttachment, ItemMovementLog, ScheduledMaintenance,
    TaskQueue
)

# --- تنظیمات نمایش برای مدل Partner (شرکت‌ها / طرف حساب‌ها) ---
@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'contact_person', 'phone', 'email']
    search_fields = ['name', 'contact_person']
    list_filter = ['type']


# --- نمایش کالا / تجهیز ---
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'status', 'current_location', 'serial_number']
    list_filter = ['category', 'status', 'is_consumable', 'is_loanable']
    search_fields = ['name', 'model', 'brand', 'serial_number', 'barcode']


# --- موجودی ---
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'location', 'expiration_date']
    list_filter = ['location']
    search_fields = ['item__name', 'location']
    autocomplete_fields = ['item']


# --- ورود به انبار ---
class StockInItemInline(admin.TabularInline):
    model = StockInItem
    extra = 1


@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'supplier', 'invoice_number']
    inlines = [StockInItemInline]
    autocomplete_fields = ['supplier']


# --- خروج از انبار ---
class StockOutItemInline(admin.TabularInline):
    model = StockOutItem
    extra = 1


@admin.register(StockOut)
class StockOutAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'department', 'staff']
    inlines = [StockOutItemInline]


# --- امانت تجهیزات ---
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['item', 'patient', 'loan_date', 'expected_return_date', 'return_date', 'status']
    list_filter = ['status']
    search_fields = ['item__name', 'patient', 'external_patient_id']
    autocomplete_fields = ['item']


# --- استفاده از تجهیز توسط بیمار ---
@admin.register(PatientUsageLog)
class PatientUsageLogAdmin(admin.ModelAdmin):
    list_display = ['item', 'patient', 'date', 'performed_by']
    search_fields = ['item__name', 'patient', 'performed_by']


# --- تعمیرات ---
@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['item', 'status', 'date_reported', 'maintenance_date', 'company', 'cost']
    list_filter = ['status']
    autocomplete_fields = ['item', 'company']


# --- کالیبراسیون ---
@admin.register(CalibrationLog)
class CalibrationLogAdmin(admin.ModelAdmin):
    list_display = ['item', 'calibration_date', 'expiration_date', 'performed_by']
    autocomplete_fields = ['item', 'performed_by']


# --- اسقاط ---
@admin.register(DecommissionLog)
class DecommissionLogAdmin(admin.ModelAdmin):
    list_display = ['item', 'date', 'confirmed_by']
    search_fields = ['item__name', 'confirmed_by']


# --- تاریخچه وضعیت ---
@admin.register(ItemStatusHistory)
class ItemStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['item', 'status', 'change_date', 'changed_by']
    list_filter = ['status']
    search_fields = ['item__name', 'changed_by']


# --- ضمائم فایل‌ها ---
@admin.register(DocumentAttachment)
class DocumentAttachmentAdmin(admin.ModelAdmin):
    list_display = ['item', 'doc_type', 'uploaded_by', 'upload_date']
    list_filter = ['doc_type']
    search_fields = ['item__name', 'uploaded_by']


# --- لاگ جابجایی ---
@admin.register(ItemMovementLog)
class ItemMovementLogAdmin(admin.ModelAdmin):
    list_display = ['item', 'from_location', 'to_location', 'moved_by', 'move_date']
    search_fields = ['item__name', 'from_location', 'to_location', 'moved_by']


# --- نگهداری برنامه‌ریزی‌شده ---
@admin.register(ScheduledMaintenance)
class ScheduledMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['item', 'next_due_date', 'assigned_to', 'status']
    list_filter = ['status']
    search_fields = ['item__name', 'assigned_to']


# --- کارتابل وظایف ---
@admin.register(TaskQueue)
class TaskQueueAdmin(admin.ModelAdmin):
    list_display = ['task_type', 'related_item', 'due_date', 'assigned_to', 'status', 'auto_generated']
    list_filter = ['task_type', 'status', 'auto_generated']
    search_fields = ['related_item__name', 'assigned_to']
    autocomplete_fields = ['related_item']