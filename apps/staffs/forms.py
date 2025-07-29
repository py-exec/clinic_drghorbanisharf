from django import forms

from .models import (
    StaffPosition,
    Staff,
    AttendanceRecord,
    LeaveRequest,
    ShiftAssignment,
    DailyWorkLog
)


# ----------------------------
# فرم موقعیت شغلی
# ----------------------------
class StaffPositionForm(forms.ModelForm):
    class Meta:
        model = StaffPosition
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


# ----------------------------
# فرم ثبت کارمند
# ----------------------------
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = [
            'user',
            'position',
            'contract_number',
            'contract_start',
            'contract_end',
            'contract_file',
            'base_salary',
            'is_active',
            'notes',
        ]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "position": forms.Select(attrs={"class": "form-select"}),
            "contract_number": forms.TextInput(attrs={"class": "form-control"}),
            "contract_start": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "contract_end": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "contract_file": forms.FileInput(attrs={"class": "form-control"}),
            "base_salary": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


# ----------------------------
# فرم حضور و غیاب
# ----------------------------
class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ["staff", "date", "clock_in", "clock_out", "method", "note"]
        widgets = {
            "staff": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "clock_in": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "clock_out": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "method": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


# ----------------------------
# فرم درخواست مرخصی
# ----------------------------
class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = [
            "staff",
            "leave_type",
            "start_date",
            "end_date",
            "reason",
            "status",
            "reviewed_by"
        ]
        widgets = {
            "staff": forms.Select(attrs={"class": "form-select"}),
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "reviewed_by": forms.Select(attrs={"class": "form-select"}),
        }


# ----------------------------
# فرم تخصیص شیفت
# ----------------------------
class ShiftAssignmentForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ["staff", "shift", "assigned_by"]
        widgets = {
            "staff": forms.Select(attrs={"class": "form-select"}),
            "shift": forms.Select(attrs={"class": "form-select"}),
            "assigned_by": forms.Select(attrs={"class": "form-select"}),
        }


# ----------------------------
# فرم گزارش روزانه کاری
# ----------------------------
class DailyWorkLogForm(forms.ModelForm):
    class Meta:
        model = DailyWorkLog
        fields = [
            "staff",
            "date",
            "shift",
            "worked_hours",
            "overtime_hours",
            "is_late",
            "left_early",
            "notes",
            "confirmed_by"
        ]
        widgets = {
            "staff": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "shift": forms.Select(attrs={"class": "form-select"}),
            "worked_hours": forms.NumberInput(attrs={"class": "form-control"}),
            "overtime_hours": forms.NumberInput(attrs={"class": "form-control"}),
            "is_late": forms.CheckboxInput(),
            "left_early": forms.CheckboxInput(),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "confirmed_by": forms.Select(attrs={"class": "form-select"}),
        }
