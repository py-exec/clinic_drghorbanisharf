# apps/reception/views.py

import jdatetime
import logging
from apps.accounting.models import Invoice, InvoiceItem, Transaction
from apps.patient.models import Patient
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, DeleteView

from .forms import ReceptionForm, PatientLookupForm
from .forms_service import ServiceTypeForm, ServiceTariffForm
from .models import Reception, ReceptionService, ServiceTariff, ServiceType, Location
from .utils import get_tariff_cached
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as drf_status
from apps.reception.models import ReceptionServiceStatus
from apps.reception.models import ReceptionService
from apps.reception.status_service import change_service_status


class ChangeReceptionServiceStatusAPIView(LoginRequiredMixin, PermissionRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, service_id):
        new_status = request.data.get("status")
        note = request.data.get("note", "")

        if not new_status:
            return Response({"error": "فیلد وضعیت اجباری است."}, status=drf_status.HTTP_400_BAD_REQUEST)

        valid_statuses = [s[0] for s in ReceptionServiceStatus.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": "وضعیت نامعتبر است."}, status=drf_status.HTTP_400_BAD_REQUEST)

        try:
            service = ReceptionService.objects.select_related("tariff__service_type", "reception__patient__user").get(
                pk=service_id)
        except ReceptionService.DoesNotExist:
            return Response({"error": "خدمت پیدا نشد."}, status=drf_status.HTTP_404_NOT_FOUND)

        changed = change_service_status(service, new_status, user=request.user, note=note)

        if changed:
            # 🔽 اینجا اضافه کن:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()

            # 📢 مثلاً گروهی بر اساس نقش مسئول خدمت (برای تفکیک افراد)
            group_name = f"role_{service.tariff.service_type.assigned_role.code}"

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "reception_update",  # → نوع پیام، باید در consumer هندل شود
                    "action": "status_changed",
                    "service_id": service.id,
                    "new_status": new_status,
                    "status_display": service.get_status_display(),
                    "reception_id": service.reception_id,
                    "service_type": service.tariff.service_type.name,
                    "changed_by": request.user.get_full_name(),
                }
            )

        return Response({
            "success": changed,
            "service_id": service.id,
            "new_status": new_status,
            "status_display": service.get_status_display(),
            "note": note,
            "changed_by": request.user.get_full_name(),
            "message": "وضعیت با موفقیت تغییر کرد." if changed else "وضعیت تغییری نکرد (تکراری بود)."
        }, status=drf_status.HTTP_200_OK)


# --- Class-Based Views for Reception CRUD ---

class ReceptionStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "reception/reception_start.html"
    permission_required = "reception.add_reception"
    raise_exception = True  # اگر دسترسی نداشت 403 بده

    def get(self, request, *args, **kwargs):
        form = PatientLookupForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = PatientLookupForm(request.POST)
        if not form.is_valid():
            messages.error(request, "لطفاً حداقل یکی از فیلدهای جستجو را وارد کنید.")
            return render(request, self.template_name, {"form": form})

        national_code = form.cleaned_data.get("national_code")
        phone_number = form.cleaned_data.get("phone_number")
        record_number = form.cleaned_data.get("record_number")

        # جستجوی بیمار بر اساس اولویت
        patient = None
        try:
            if national_code:
                patient = Patient.objects.select_related("user").filter(user__national_code=national_code).first()
            elif phone_number:
                patient = Patient.objects.select_related("user").filter(user__phone_number=phone_number).first()
            elif record_number:
                patient = Patient.objects.filter(record_number=record_number).first()

        except Exception as e:
            messages.error(request, "❌ در فرآیند جستجوی بیمار خطایی رخ داد.")
            return render(request, self.template_name, {"form": form})

        if patient:
            # اگر بیمار پیدا شد، هدایت به صفحه ثبت پذیرش
            messages.success(request, f"✅ بیمار {patient.user.get_full_name()} پیدا شد.")
            return redirect(reverse("reception:create", kwargs={"patient_id": patient.pk}))
        else:
            # اگر بیمار پیدا نشد، هدایت به صفحه ایجاد بیمار
            messages.warning(request, "کاربری با این اطلاعات یافت نشد. لطفاً بیمار جدیدی ثبت کنید.")
            return redirect(reverse("patient:patient_create"))


class ReceptionCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "reception/reception_form.html"
    permission_required = "reception.add_reception"
    raise_exception = True  # برای نمایش 403 اگر دسترسی نداشته باشد

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        print("📤 [GET] Rendering context for reception form:", flush=True)
        print(f"🧾 Patient: {context['patient']}", flush=True)
        print(f"📦 Services count: {context['form'].fields['services'].queryset.count()}", flush=True)
        print(f"💰 Tariff Map: {context['service_tariff_map']}", flush=True)

        return render(request, self.template_name, context)

    def dispatch(self, request, *args, **kwargs):
        self.patient = get_object_or_404(Patient, pk=kwargs.get("patient_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, form=None):
        form = form or ReceptionForm()

        print("🧊 [FORM INIT] queryset count:", form.fields['services'].queryset.count(), flush=True)

        # 👇 اضافه کن این قسمت برای چاپ دقیق محتوا
        for service in form.fields['services'].queryset:
            print(f"🔹 {service.pk} | {service.service_type.name} | {service.amount} | __str__: {str(service)}",
                  flush=True)

        return {
            "form": form,
            "patient": self.patient,
            "service_tariff_map": {
                str(t.id): t.amount for t in form.fields['services'].queryset
            }
        }

    def post(self, request, *args, **kwargs):
        self.patient = get_object_or_404(Patient, pk=kwargs.get("patient_id"))
        form = ReceptionForm(request.POST, patient=self.patient)

        print(f"📥 Raw POST Data: {dict(request.POST)}", flush=True)

        if not form.is_valid():
            print(f"❌ Form Errors: {form.errors.as_data()}", flush=True)
            messages.error(request, "لطفاً خطاهای فرم را اصلاح کنید.")
            return render(request, self.template_name, self.get_context_data(form))

        print(f"✅ Cleaned Data: {form.cleaned_data}", flush=True)

        try:
            with transaction.atomic():
                reception = self._create_reception(form)
                invoice = self._create_invoice(reception, form.cleaned_data)
                self._create_transactions(invoice, form.cleaned_data)
                self._send_sms(reception)

                messages.success(request, f"✅ پذیرش برای {self.patient.user.get_full_name()} ثبت شد.")
                return redirect(reverse("reception:detail", kwargs={"pk": reception.pk}))

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"💥 Exception occurred in ReceptionCreateView.post(): {e}", flush=True)
            messages.error(request, "در فرآیند ثبت پذیرش خطایی رخ داد. لطفاً مجدداً تلاش کنید.")
            return render(request, self.template_name, self.get_context_data(form))

    def _create_reception(self, form):
        reception = form.save(commit=False)
        reception.patient = self.patient
        reception.created_by = self.request.user
        reception.receptionist = self.request.user
        reception.save()

        # ذخیره‌ی خدمات انتخاب‌شده
        services = form.cleaned_data.get("services", [])
        for tariff in services:
            ReceptionService.objects.create(
                reception=reception,
                tariff=tariff,
                created_by=self.request.user
            )

        return reception

    def _create_invoice(self, reception, cleaned_data):
        invoice = Invoice.objects.create(
            related_user=self.patient.user,
            related_reception=reception,
            created_by=self.request.user,
            status="draft",
        )

        for service in cleaned_data.get("services", []):
            InvoiceItem.objects.create(
                invoice=invoice,
                service_tariff=service,
                quantity=1,
                unit_price=service.amount,
            )

        invoice.status = "open"
        invoice.save()
        return invoice

    def _create_transactions(self, invoice, cleaned_data):
        for method in ['cash', 'card', 'online']:
            amount = cleaned_data.get(f'{method}_amount') or 0
            if amount > 0:
                Transaction.objects.create(
                    invoice=invoice,
                    related_reception=invoice.related_reception,
                    related_user=self.patient.user,
                    transaction_type='inflow',
                    payment_method=method,
                    amount=amount,
                    created_by=self.request.user,
                )

    def _send_sms(self, reception):
        # ⚠️ این بخش در آینده باید به Celery منتقل شود
        phone = reception.patient.user.phone_number
        print(f"📤 [SMS TEST] پیامک به {phone} برای پذیرش {reception.pk}")


class ReceptionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Reception
    template_name = "reception/reception_list.html"
    context_object_name = "receptions"
    permission_required = "reception.view_reception"
    paginate_by = 15

    def get_queryset(self):
        queryset = Reception.objects.select_related(
            "patient__user", "location", "receptionist"
        ).prefetch_related(
            "services__tariff__service_type"
        ).order_by("-admission_date")

        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(patient__user__first_name__icontains=search_query) |
                Q(patient__user__last_name__icontains=search_query) |
                Q(patient__user__phone_number__icontains=search_query) |
                Q(patient__user__national_code__icontains=search_query) |
                Q(admission_code__icontains=search_query)
            )
        return queryset


class ReceptionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Reception
    template_name = "reception/reception_detail.html"
    context_object_name = "reception"
    permission_required = "reception.view_reception"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reception = self.get_object()

        try:
            j_date = jdatetime.datetime.fromgregorian(datetime=reception.admission_date)
            context['jalali_date'] = j_date.strftime("%Y/%m/%d - %H:%M")
        except:
            context['jalali_date'] = "—"

        # 💰 یافتن فاکتور مرتبط با پذیرش
        invoice = getattr(reception, "invoice", None)
        total = 0
        paid = 0

        if invoice:
            total = invoice.final_amount or 0
            paid = invoice.paid_amount or 0

        context["total_cost"] = total
        context["paid_amount"] = paid
        context["remaining_amount"] = total - paid

        return context


class ReceptionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Reception
    form_class = ReceptionForm
    template_name = "reception/reception_form.html"
    permission_required = "reception.change_reception"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = self.object.patient
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()

                # پاک کردن خدمات قبلی
                self.object.services.all().delete()  # ← اصلاح شد

                # ساخت خدمات جدید
                for service in form.cleaned_data["services"]:
                    ReceptionService.objects.create(
                        reception=self.object,
                        tariff=service,
                        cost=service.amount,  # ← این مقدار مشکلی نداره چون amount در Tariff هست
                        created_by=self.request.user  # ← (اختیاری) اگر ست می‌کنی
                    )

                messages.success(self.request, "پذیرش با موفقیت ویرایش شد.")
                return redirect(self.get_success_url())

        except Exception as e:
            import traceback
            print("⛔ Exception:", e)
            print(traceback.format_exc())
            logging.exception("⛔ خطا در ویرایش پذیرش")
            messages.error(self.request, "ویرایش با خطا مواجه شد.")
            return self.form_invalid(form)


def get_success_url(self):
    return self.object.get_absolute_url()


class ReceptionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Reception
    template_name = "reception/reception_confirm_delete.html"
    permission_required = "reception.delete_reception"
    success_url = reverse_lazy("reception:list")

    def form_valid(self, form):
        messages.warning(self.request, f"پذیرش «{self.object.admission_code}» با موفقیت حذف شد.")
        return super().form_valid(form)


# --- سایر توابع (API و عملیات خاص) ---

@login_required
@permission_required("reception.add_reception", raise_exception=True)
def add_service_to_reception(request, reception_id):
    """
    View برای افزودن یک خدمت جدید به یک پذیرش موجود.
    """
    reception = get_object_or_404(Reception, pk=reception_id)
    if request.method == "POST":
        form = ReceptionServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.reception = reception
            service.created_by = request.user
            if service.tariff:
                service.cost = service.tariff.amount
            service.save()
            messages.success(request, "خدمت جدید با موفقیت به پذیرش اضافه شد.")
            return redirect(reception.get_absolute_url())
    else:
        form = ReceptionServiceForm()

    return render(request, "reception/add_service_form.html", {
        "form": form,
        "reception": reception,
    })


@require_POST
@login_required
@permission_required("reception.change_reception", raise_exception=True)
def mark_service_done(request, service_id):
    """
    سرویس را به وضعیت "انجام شده" تغییر می‌دهد.
    """
    service = get_object_or_404(ReceptionService, id=service_id)
    service.status = "done"
    service.done_at = timezone.now()
    service.performed_by_staff = request.user
    service.save()
    messages.success(request, f"خدمت '{service.tariff.service_type.name}' انجام شد.")
    return redirect(service.reception.get_absolute_url())


@login_required
@permission_required("reception.change_reception", raise_exception=True)
def cancel_service(request, service_id):
    """
    یک خدمت را کنسل می‌کند و دلیل آن را ثبت می‌کند.
    """
    service = get_object_or_404(ReceptionService, id=service_id)
    if request.method == "POST":
        reason = request.POST.get("cancel_reason", "").strip()
        if not reason:
            messages.error(request, "برای کنسل کردن خدمت، ارائه دلیل الزامی است.")
        else:
            service.status = "cancelled"
            service.cancel_reason = reason
            service.cancelled_at = timezone.now()
            service.save()
            messages.warning(request, f"خدمت '{service.tariff.service_type.name}' کنسل شد.")
        return redirect(service.reception.get_absolute_url())

    return render(request, "reception/cancel_service_form.html", {"service": service})


@login_required
@permission_required("accounting.add_invoice", raise_exception=True)
def confirm_payment(request, pk):
    """
    به جای انجام پرداخت، کاربر را به صفحه ایجاد فاکتور برای این پذیرش هدایت می‌کند.
    """
    reception = get_object_or_404(Reception, pk=pk)
    # ساخت URL برای ایجاد فاکتور با پارامتر پذیرش
    create_invoice_url = reverse('accounting:invoice_create') + f'?reception_id={reception.id}'
    messages.info(request, "شما به صفحه ایجاد فاکتور برای این پذیرش هدایت شدید.")
    return redirect(create_invoice_url)


@login_required
@permission_required("reception.view_reception", raise_exception=True)
def get_service_cost_api(request):
    """
    API برای دریافت هزینه یک تعرفه مشخص.
    """
    tariff_id = request.GET.get("tariff_id")
    if not tariff_id:
        return JsonResponse({"cost": 0})
    try:
        tariff = ServiceTariff.objects.get(id=tariff_id)
        return JsonResponse({"cost": tariff.amount})
    except ServiceTariff.DoesNotExist:
        return JsonResponse({"cost": 0})


@login_required
@permission_required("reception.view_reception", raise_exception=True)
def reception_services_api(request, pk):
    """
    API برای دریافت لیست خدمات یک پذیرش مشخص.
    """
    reception = get_object_or_404(Reception, pk=pk)
    services = reception.services.select_related('tariff__service_type').order_by("created_at")
    data = [{
        "id": s.id,
        "service_name": s.tariff.service_type.name,
        "tracking_code": s.tracking_code,
        "cost": s.cost,
        "status": s.get_status_display(),
        "status_code": s.status,
    } for s in services]
    return JsonResponse({"services": data})


@login_required
@permission_required("reception.view_reception", raise_exception=True)
def reception_table_partial(request):
    """
    View برای رندر کردن بخش جدول پذیرش‌ها (برای استفاده با HTMX/Ajax).
    """
    # این تابع از get_queryset در ReceptionListView استفاده می‌کند تا منطق تکراری نشود
    list_view = ReceptionListView()
    list_view.request = request
    queryset = list_view.get_queryset()

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'receptions': page_obj.object_list, 'page_obj': page_obj}
    return render(request, "reception/partials/_reception_table.html", context)


# --- ServiceType CRUD Views ---

class ServiceTypeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ServiceType
    template_name = "reception/service_type_list.html"
    context_object_name = "services"
    permission_required = "reception.view_servicetype"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "لیست خدمات",
        })
        return context


class ServiceTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = "reception/service_type_form.html"
    success_url = reverse_lazy("reception:service_list")
    permission_required = "reception.add_servicetype"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "ایجاد خدمت جدید"
        context["list_url"] = reverse("reception:service_list")
        return context


class ServiceTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = "reception/service_type_form.html"
    success_url = reverse_lazy("reception:service_list")
    permission_required = "reception.change_servicetype"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"ویرایش خدمت: {self.object.name}"
        context["list_url"] = reverse("reception:service_list")
        return context


class ServiceTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ServiceType
    template_name = "reception/service_type_confirm_delete.html"
    success_url = reverse_lazy("reception:service_list")
    permission_required = "reception.delete_servicetype"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("reception:service_list")
        return context


# --- ServiceTariff CRUD Views ---

class ServiceTariffListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ServiceTariff
    template_name = "reception/service_tariff_list.html"
    context_object_name = "tariffs"
    permission_required = "reception.view_servicetariff"
    paginate_by = 10  # اضافه شده: برای فعال کردن pagination، هر صفحه ۱۰ مورد

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '').strip()  # .strip() برای حذف فضای خالی
        service_type_id = self.request.GET.get('service_type', '').strip()

        if search_query:
            # جستجو بر اساس نام خدمت مربوطه یا مبلغ تعرفه
            # Q(service_type__name__icontains=search_query): جستجو در نام نوع خدمت
            # Q(amount__icontains=search_query): جستجو در مبلغ (باید string باشد)
            # اگر مبلغ عدد است و در DB عدد ذخیره شده، این ممکن است به خوبی کار نکند
            # می توانیم سعی کنیم به عدد تبدیل کنیم
            queryset = queryset.filter(
                Q(service_type__name__icontains=search_query) |
                Q(amount__icontains=search_query)
            )

        if service_type_id:
            try:
                # تبدیل service_type_id به عدد صحیح برای فیلتر
                service_type_id = int(service_type_id)
                queryset = queryset.filter(service_type__id=service_type_id)
            except ValueError:
                # اگر service_type_id معتبر نبود، فیلتر اعمال نشود
                pass

        # مرتب سازی: معمولا بر اساس تاریخ اعتبار جدیدتر یا نام خدمت
        return queryset.order_by('-valid_from',
                                 'service_type__name')  # مرتب سازی بر اساس تاریخ اعتبار جدیدتر و نام خدمت

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "لیست تعرفه‌ها"
        # اضافه کردن لیست تمام ServiceType های فعال برای استفاده در فیلتر Dropdown در قالب
        context["service_types_for_filter"] = ServiceType.objects.filter(is_active=True).order_by('name')

        # اضافه کردن مقادیر فیلترهای فعلی برای نمایش در فرم
        context["current_search"] = self.request.GET.get('search', '')
        context["current_service_type_id"] = self.request.GET.get('service_type', '')

        return context


class ServiceTariffCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ServiceTariff
    form_class = ServiceTariffForm
    template_name = "reception/service_tariff_form.html"
    success_url = reverse_lazy("reception:tariff_list")
    permission_required = "reception.add_servicetariff"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "ایجاد تعرفه جدید"
        context["list_url"] = reverse("reception:tariff_list")
        return context


class ServiceTariffUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceTariff
    form_class = ServiceTariffForm
    template_name = "reception/service_tariff_form.html"
    success_url = reverse_lazy("reception:tariff_list")
    permission_required = "reception.change_servicetariff"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"ویرایش تعرفه: {self.object.service_type.name}"
        context["list_url"] = reverse("reception:tariff_list")
        return context


class ServiceTariffDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ServiceTariff
    template_name = "reception/service_tariff_confirm_delete.html"
    success_url = reverse_lazy("reception:tariff_list")
    permission_required = "reception.delete_servicetariff"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("reception:tariff_list")
        return context
