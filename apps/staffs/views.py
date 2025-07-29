import pandas as pd
import tempfile
from apps.accounts.mixins import RoleRequiredMixin
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from io import BytesIO
from weasyprint import HTML

from .forms import (
    StaffForm,
    StaffPositionForm,
    AttendanceRecordForm,
    LeaveRequestForm,
    ShiftAssignmentForm,
    DailyWorkLogForm
)
from .models import (
    Staff,
    StaffPosition,
    AttendanceRecord,
    LeaveRequest,
    ShiftAssignment,
    DailyWorkLog
)


@login_required
def staff_report_pdf(request):
    staffs = Staff.objects.filter(is_active=True).select_related("user", "position")

    html_string = render_to_string("staffs/pdf/staff_report.html", {
        "staffs": staffs,
        "date": datetime.now()
    })

    # تولید فایل PDF از HTML
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename="staff_report.pdf"'

    # ایجاد فایل موقت برای PDF
    with tempfile.NamedTemporaryFile(delete=True) as output:
        HTML(string=html_string).write_pdf(output.name)
        output.seek(0)
        response.write(output.read())

    return response


@login_required
def staff_report_excel(request):
    staffs = Staff.objects.filter(is_active=True).select_related("user", "position")

    data = []
    for staff in staffs:
        data.append({
            "نام": staff.user.get_full_name(),
            "کد ملی": staff.user.national_code,
            "موقعیت": staff.position.title if staff.position else "-",
            "وضعیت": "فعال" if staff.is_active else "غیرفعال",
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Staff Report", index=False)

    output.seek(0)
    filename = f"staff_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(
        output,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class StaffSearchView(ListView):
    model = Staff
    template_name = "staffs/staff_search.html"
    context_object_name = "staffs"

    def get_queryset(self):
        query = self.request.GET.get("q")
        qs = Staff.objects.filter(is_active=True)
        if query:
            qs = qs.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(position__title__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


# ----------------------------
# لیست کارمندان
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffListView(ListView):
    model = Staff
    template_name = "staffs/staff_list.html"
    context_object_name = "staffs"


# ----------------------------
# ساخت کارمند
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffCreateView(CreateView):
    model = Staff
    form_class = StaffForm
    template_name = "staffs/staff_form.html"
    success_url = reverse_lazy("staffs:staff-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ کارمند جدید با موفقیت ثبت شد.")
        return super().form_valid(form)


# ----------------------------
# ویرایش کارمند
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffUpdateView(UpdateView):
    model = Staff
    form_class = StaffForm
    template_name = "staffs/staff_form.html"
    success_url = reverse_lazy("staffs:staff-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ اطلاعات کارمند بروزرسانی شد.")
        return super().form_valid(form)


# ----------------------------
# حذف نرم کارمند
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffDeleteView(DeleteView):
    model = Staff
    template_name = "staffs/staff_confirm_delete.html"
    success_url = reverse_lazy("staffs:staff-list")

    def delete(self, request, *args, **kwargs):
        staff = self.get_object()
        staff.soft_delete()
        messages.warning(request, "⚠️ کارمند غیرفعال شد.")
        return redirect(self.success_url)


# ----------------------------
# لیست موقعیت‌های شغلی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffPositionListView(ListView):
    model = StaffPosition
    template_name = "staffs/position_list.html"
    context_object_name = "positions"


# ----------------------------
# ایجاد موقعیت شغلی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffPositionCreateView(CreateView):
    model = StaffPosition
    form_class = StaffPositionForm
    template_name = "staffs/position_form.html"
    success_url = reverse_lazy("staffs:position-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ موقعیت شغلی با موفقیت ثبت شد.")
        return super().form_valid(form)


# ----------------------------
# ویرایش موقعیت شغلی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffPositionUpdateView(UpdateView):
    model = StaffPosition
    form_class = StaffPositionForm
    template_name = "staffs/position_form.html"
    success_url = reverse_lazy("staffs:position-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ موقعیت شغلی بروزرسانی شد.")
        return super().form_valid(form)


# ----------------------------
# حذف موقعیت شغلی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class StaffPositionDeleteView(DeleteView):
    model = StaffPosition
    template_name = "staffs/position_confirm_delete.html"
    success_url = reverse_lazy("staffs:position-list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ موقعیت شغلی حذف شد.")
        return super().delete(request, *args, **kwargs)


# ----------------------------
# لیست حضور و غیاب
# ----------------------------
@method_decorator(login_required, name='dispatch')
class AttendanceRecordListView(ListView):
    model = AttendanceRecord
    template_name = "staffs/attendance_list.html"
    context_object_name = "records"


# ----------------------------
# ثبت حضور و غیاب
# ----------------------------
@method_decorator(login_required, name='dispatch')
class AttendanceRecordCreateView(CreateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = "staffs/attendance_form.html"
    success_url = reverse_lazy("staffs:attendance-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ حضور ثبت شد.")
        return super().form_valid(form)


# ----------------------------
# ویرایش رکورد حضور
# ----------------------------
@method_decorator(login_required, name='dispatch')
class AttendanceRecordUpdateView(UpdateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = "staffs/attendance_form.html"
    success_url = reverse_lazy("staffs:attendance-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ اطلاعات حضور بروزرسانی شد.")
        return super().form_valid(form)


# ----------------------------
# حذف رکورد حضور
# ----------------------------
@method_decorator(login_required, name='dispatch')
class AttendanceRecordDeleteView(DeleteView):
    model = AttendanceRecord
    template_name = "staffs/attendance_confirm_delete.html"
    success_url = reverse_lazy("staffs:attendance-list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ رکورد حضور حذف شد.")
        return super().delete(request, *args, **kwargs)


# ----------------------------
# نمایش جزئیات کارمند
# ----------------------------
class StaffDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Staff
    template_name = "staffs/staff_detail.html"
    context_object_name = "staff"
    required_roles = ["admin", "hr"]


# ----------------------------
# غیرفعال‌سازی (حذف نرم) کارمند
# ----------------------------
class StaffSoftDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Staff
    template_name = "staffs/staff_confirm_delete.html"
    success_url = reverse_lazy("staffs:staff-list")
    required_roles = ["admin", "hr"]

    def delete(self, request, *args, **kwargs):
        staff = self.get_object()
        staff.soft_delete()
        messages.warning(self.request, "⛔ کارمند غیرفعال شد.")
        return redirect(self.success_url)


# ----------------------------
# فعال‌سازی مجدد کارمند
# ----------------------------
@login_required
@permission_required("reactivate_staff")
def reactivate_staff_view(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    staff.is_active = True
    staff.save(update_fields=["is_active"])
    messages.success(request, "✅ کارمند دوباره فعال شد.")
    return redirect("staffs:staff-list")


# ----------------------------
# لیست مرخصی‌ها
# ----------------------------
@method_decorator(login_required, name='dispatch')
class LeaveRequestListView(ListView):
    model = LeaveRequest
    template_name = "staffs/leave_list.html"
    context_object_name = "leaves"


# ----------------------------
# ثبت مرخصی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class LeaveRequestCreateView(CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "staffs/leave_form.html"
    success_url = reverse_lazy("staffs:leave-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ مرخصی ثبت شد.")
        return super().form_valid(form)


# ----------------------------
# ویرایش مرخصی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class LeaveRequestUpdateView(UpdateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "staffs/leave_form.html"
    success_url = reverse_lazy("staffs:leave-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ اطلاعات مرخصی بروزرسانی شد.")
        return super().form_valid(form)


# ----------------------------
# حذف مرخصی
# ----------------------------
@method_decorator(login_required, name='dispatch')
class LeaveRequestDeleteView(DeleteView):
    model = LeaveRequest
    template_name = "staffs/leave_confirm_delete.html"
    success_url = reverse_lazy("staffs:leave-list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ درخواست مرخصی حذف شد.")
        return super().delete(request, *args, **kwargs)


# ----------------------------
# لیست گزارش‌های روزانه
# ----------------------------
@method_decorator(login_required, name='dispatch')
class DailyWorkLogListView(ListView):
    model = DailyWorkLog
    template_name = "staffs/log_list.html"
    context_object_name = "logs"


# ----------------------------
# ثبت گزارش جدید
# ----------------------------
@method_decorator(login_required, name='dispatch')
class DailyWorkLogCreateView(CreateView):
    model = DailyWorkLog
    form_class = DailyWorkLogForm
    template_name = "staffs/log_form.html"
    success_url = reverse_lazy("staffs:log-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ گزارش روزانه ثبت شد.")
        return super().form_valid(form)


# ----------------------------
# ویرایش گزارش روزانه
# ----------------------------
@method_decorator(login_required, name='dispatch')
class DailyWorkLogUpdateView(UpdateView):
    model = DailyWorkLog
    form_class = DailyWorkLogForm
    template_name = "staffs/log_form.html"
    success_url = reverse_lazy("staffs:log-list")

    def form_valid(self, form):
        messages.success(self.request, "✅ گزارش روزانه بروزرسانی شد.")
        return super().form_valid(form)


# ----------------------------
# حذف گزارش روزانه
# ----------------------------
@method_decorator(login_required, name='dispatch')
class DailyWorkLogDeleteView(DeleteView):
    model = DailyWorkLog
    template_name = "staffs/log_confirm_delete.html"
    success_url = reverse_lazy("staffs:log-list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ گزارش حذف شد.")
        return super().delete(request, *args, **kwargs)
