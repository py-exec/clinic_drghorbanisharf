# apps/clinic_messenger/views_sms.py
import json
import logging
from apps.accounts.models import User, Role
from apps.appointments.models import Appointment
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import UpdateView, ListView, CreateView, DeleteView

from .forms import SMSConfigForm, SMSMessageForm, SMSPatternForm, SMSPatternTypeForm, SMSPatternVariableFormSet
from .models import SMSPattern, SMSConfig, SMSPatternType, SMSMessage
from .sms import get_ippanel_status, send_sms, send_sms_pattern
from .tasks import send_sms_async

logger = logging.getLogger(__name__)


# --- داشبورد و وضعیت ---

@login_required
@permission_required("clinic_messenger.view_smsconfig", raise_exception=True)
def sms_dashboard_view(request):
    active_configs = SMSConfig.objects.filter(is_active=True)
    sms_status_list = [
        {"config": config, "status": get_ippanel_status(config)}
        for config in active_configs
    ]

    context = {
        "sms_status_list": sms_status_list,
        "configs": SMSConfig.objects.all().order_by("-updated_at"),
        "patterns": SMSPattern.objects.select_related("config", "type").all().order_by("-created_at"),
        "pattern_types": SMSPatternType.objects.all().order_by("title"),
    }
    return render(request, "clinic_messenger/sms_dashboard.html", context)


@login_required
@permission_required("clinic_messenger.view_smsconfig", raise_exception=True)
def sms_status_view(request):
    active_config = SMSConfig.objects.filter(is_active=True).first()
    status = get_ippanel_status(active_config) if active_config else {"success": False,
                                                                      "message": "هیچ تنظیم فعالی یافت نشد."}
    return render(request, "clinic_messenger/sms_status.html", {
        "status": status,
        "active_config": active_config
    })


# --- ارسال و تست پیامک ---

@login_required
@permission_required("clinic_messenger.add_smsmessage", raise_exception=True)
def sms_send_view(request):
    if request.method == "POST":
        form = SMSMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.requested_by = request.user
            message.purpose = 'manual'
            send_sms_async.delay(to=message.to, text=message.body)
            message.status = "pending"
            message.save()
            messages.success(request, f"پیامک برای شماره {message.to} با موفقیت در صف ارسال قرار گرفت.")
            return redirect("clinic_messenger:sms_send")
    else:
        form = SMSMessageForm()
    return render(request, "clinic_messenger/sms_send.html", {"form": form})


@login_required
@permission_required("clinic_messenger.add_smsmessage", raise_exception=True)
def sms_send_bulk_view(request):
    if request.method == "POST":
        recipient_group = request.POST.get('recipient_group')
        body_template = request.POST.get('body')
        appointment_date_str = request.POST.get('appointment_date')

        if not recipient_group or not body_template:
            messages.error(request, "گروه گیرندگان و متن پیام الزامی است.")
            return redirect("clinic_messenger:sms_send")

        recipients = User.objects.none()

        if recipient_group == 'all_patients':
            recipients = User.objects.filter(role__code='patient', is_active=True)
        elif recipient_group == 'all_doctors':
            recipients = User.objects.filter(role__code='doctor', is_active=True)
        elif recipient_group == 'all_staff':
            recipients = User.objects.filter(role__code__in=['staff', 'receptionist'], is_active=True)
        elif recipient_group == 'patients_with_appointment':
            if not appointment_date_str:
                messages.error(request, "برای این گروه، انتخاب تاریخ نوبت الزامی است.")
                return redirect("clinic_messenger:sms_send")
            try:
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                appointments = Appointment.objects.filter(date=appointment_date).select_related('patient__user')
                recipients = User.objects.filter(patient_profile__in=[app.patient for app in appointments])
            except (ValueError, TypeError):
                messages.error(request, "فرمت تاریخ نامعتبر است.")
                return redirect("clinic_messenger:sms_send")

        count = 0
        for user in recipients:
            if user.phone_number:
                body = body_template.replace("{{نام کامل}}", user.get_full_name())
                body = body.replace("{{نام}}", user.first_name)
                body = body.replace("{{نام خانوادگی}}", user.last_name)
                send_sms_async.delay(to=user.phone_number, text=body)
                count += 1

        messages.success(request, f"{count} پیامک با موفقیت در صف ارسال قرار گرفت.")
        return redirect("clinic_messenger:sms_send")

    return redirect("clinic_messenger:sms_send")


@csrf_exempt
@require_POST
@login_required
@permission_required("clinic_messenger.view_smspattern", raise_exception=True)
def test_pattern_view(request):
    try:
        data = json.loads(request.body)
        code = data.get("code")
        phone = data.get("phone")
        variables = data.get("variables", {})

        if not code or not phone:
            return JsonResponse({"success": False, "message": "کد پترن و شماره موبایل الزامی است."}, status=400)

        result = send_sms_pattern(to=phone, pattern_code=code, variables=variables)
        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "درخواست نامعتبر (Invalid JSON)."}, status=400)
    except Exception as e:
        logger.error(f"خطای غیرمنتظره در تست پترن: {e}")
        return JsonResponse({"success": False, "message": f"خطای سرور: {e}"}, status=500)


# --- مدیریت تنظیمات پنل (SMSConfig) ---

class SMSConfigCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SMSConfig
    form_class = SMSConfigForm
    template_name = 'clinic_messenger/sms_config_form.html'
    permission_required = 'clinic_messenger.add_smsconfig'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "تنظیمات جدید پنل پیامک با موفقیت ایجاد شد.")
        return super().form_valid(form)


class SMSConfigUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SMSConfig
    form_class = SMSConfigForm
    template_name = 'clinic_messenger/sms_config_form.html'
    permission_required = 'clinic_messenger.change_smsconfig'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "تنظیمات پنل پیامک با موفقیت ویرایش شد.")
        return super().form_valid(form)


class SMSConfigDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SMSConfig
    template_name = 'clinic_messenger/confirm_delete.html'
    permission_required = 'clinic_messenger.delete_smsconfig'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.warning(self.request, f"تنظیمات '{self.object}' حذف شد.")
        return super().form_valid(form)


# --- مدیریت پترن‌ها (SMSPattern) ---

class SMSPatternListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SMSPattern
    template_name = "clinic_messenger/sms_pattern_list.html"
    context_object_name = "patterns"
    permission_required = "clinic_messenger.view_smspattern"
    paginate_by = 20


class SMSPatternCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SMSPattern
    form_class = SMSPatternForm
    template_name = 'clinic_messenger/sms_pattern_form.html'
    permission_required = 'clinic_messenger.add_smspattern'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['variable_formset'] = SMSPatternVariableFormSet(self.request.POST)
        else:
            context['variable_formset'] = SMSPatternVariableFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        variable_formset = context['variable_formset']
        if variable_formset.is_valid():
            self.object = form.save()
            variable_formset.instance = self.object
            variable_formset.save()
            messages.success(self.request, "پترن جدید با موفقیت ایجاد شد.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class SMSPatternUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SMSPattern
    form_class = SMSPatternForm
    template_name = 'clinic_messenger/sms_pattern_form.html'
    permission_required = 'clinic_messenger.change_smspattern'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['variable_formset'] = SMSPatternVariableFormSet(self.request.POST, instance=self.object)
        else:
            context['variable_formset'] = SMSPatternVariableFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        variable_formset = context['variable_formset']
        if variable_formset.is_valid():
            self.object = form.save()
            variable_formset.instance = self.object
            variable_formset.save()
            messages.success(self.request, "پترن با موفقیت ویرایش شد.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class SMSPatternDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SMSPattern
    template_name = 'clinic_messenger/confirm_delete.html'
    permission_required = 'clinic_messenger.delete_smspattern'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.warning(self.request, f"پترن '{self.object.name}' حذف شد.")
        return super().form_valid(form)


class SMSPatternTypeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SMSPatternType
    template_name = 'clinic_messenger/sms_pattern_type_list.html'
    context_object_name = 'pattern_types'
    permission_required = 'clinic_messenger.view_smspatterntype'
    paginate_by = 20


class SMSPatternTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SMSPatternType
    form_class = SMSPatternTypeForm  # ❗️ توجه: این فرم باید در forms.py ایجاد شود
    template_name = 'clinic_messenger/sms_pattern_type_form.html'
    permission_required = 'clinic_messenger.add_smspatterntype'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "نوع پترن جدید با موفقیت ایجاد شد.")
        return super().form_valid(form)


class SMSPatternTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SMSPatternType
    form_class = SMSPatternTypeForm  # ❗️ توجه: این فرم باید در forms.py ایجاد شود
    template_name = 'clinic_messenger/sms_pattern_type_form.html'
    permission_required = 'clinic_messenger.change_smspatterntype'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "نوع پترن با موفقیت ویرایش شد.")
        return super().form_valid(form)


class SMSPatternTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SMSPatternType
    template_name = 'clinic_messenger/confirm_delete.html'
    permission_required = 'clinic_messenger.delete_smspatterntype'
    success_url = reverse_lazy('clinic_messenger:sms_dashboard')

    def form_valid(self, form):
        messages.warning(self.request, f"نوع پترن '{self.object.title}' حذف شد.")
        return super().form_valid(form)
