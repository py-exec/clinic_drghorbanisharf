# apps/patient/views.py

from apps.accounts.models import User
from apps.clinic_messenger.models import SMSPattern
from apps.clinic_messenger.sms import send_sms_pattern
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import PatientLookupForm, PatientUserForm
from .models import Patient, User


# --- فرآیند جدید جستجو و ثبت بیمار ---

@login_required
@permission_required("patient.add_patient", raise_exception=True)
def patient_lookup_view(request):
    """
    این ویو فرم جستجوی بیمار را نمایش می‌دهد و پس از ارسال، وضعیت بیمار را بررسی می‌کند.
    اگر بیمار یافت شود → به ویرایش اطلاعات هدایت می‌شود
    اگر فقط کاربر وجود داشته باشد → به فرم ایجاد بیمار با استفاده از user هدایت می‌شود
    اگر نه بیمار و نه کاربر موجود نباشد → به فرم ایجاد بیمار جدید هدایت می‌شود
    """

    # پاک کردن سشن قبلی
    request.session.pop("pending_user_id", None)

    if request.method == "POST":
        form = PatientLookupForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            user = User.objects.filter(
                Q(national_code=query) | Q(phone_number=query)
            ).first()

            if user:
                if hasattr(user, "patient_profile"):
                    # بیمار قبلاً وجود دارد → هدایت به صفحه ویرایش
                    return redirect("patient:patient_update", pk=user.patient_profile.id)
                else:
                    # فقط یوزر وجود دارد ولی بیمار نیست → ذخیره در سشن و هدایت به فرم ساخت بیمار
                    request.session["pending_user_id"] = user.id
                    return redirect("patient:patient_create")

            else:
                # هیچ کاربری وجود ندارد → فرم ساخت بیمار با مقدار اولیه
                return redirect(f"{reverse('patient:patient_create')}?query={query}")

        # اگر فرم نامعتبر بود
        messages.error(request, "ورودی نامعتبر است.")
    else:
        form = PatientLookupForm()

    return render(request, "patient/patient_lookup.html", {"form": form})


# --- مدیریت بیماران (CRUD) ---

@login_required
@permission_required("patient.add_patient", raise_exception=True)
def patient_create_view(request):
    pending_user_id = request.session.pop('pending_user_id', None)
    pending_user = None
    initial_data = {}

    # ✅ اگر از سشن اومده
    if pending_user_id:
        pending_user = get_object_or_404(User, id=pending_user_id)

        if hasattr(pending_user, 'patient_profile'):
            messages.warning(
                request,
                f"کاربر «{pending_user.get_full_name()}» قبلاً به عنوان بیمار ثبت شده است."
            )
            return redirect(pending_user.patient_profile.get_absolute_url())

        initial_data = {
            'first_name': pending_user.first_name,
            'last_name': pending_user.last_name,
            'phone_number': pending_user.phone_number,
            'national_code': pending_user.national_code,
            'email': pending_user.email,
        }

    if request.method == 'POST':
        form = PatientUserForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                patient = form.save(commit=False)

                if pending_user:
                    patient.user = pending_user
                else:
                    # بررسی کاربر موجود
                    national_code = form.cleaned_data.get("national_code")
                    phone_number = form.cleaned_data.get("phone_number")

                    existing_user = User.objects.filter(
                        Q(national_code=national_code) | Q(phone_number=phone_number)
                    ).first()

                    if existing_user:
                        if hasattr(existing_user, 'patient_profile'):
                            messages.warning(
                                request,
                                f"کاربری با کد ملی «{national_code}» و شماره «{phone_number}» قبلاً به عنوان بیمار ثبت شده است."
                            )
                            return redirect(existing_user.patient_profile.get_absolute_url())
                        else:
                            patient.user = existing_user
                    else:
                        # ایجاد کاربر جدید
                        patient.user = get_user_model().objects.create_user(
                            phone_number=phone_number,
                            national_code=national_code,
                            first_name=form.cleaned_data.get("first_name"),
                            last_name=form.cleaned_data.get("last_name"),
                            email=form.cleaned_data.get("email")
                        )

                # ذخیره بیمار
                patient.save()
                form.save_m2m()

                # ارسال پیامک در صورت تعریف پترن فعال
                pattern = SMSPattern.objects.filter(name="patient_record_created", is_active=True).first()
                if pattern:
                    try:
                        send_sms_pattern(
                            phone_number=patient.user.phone_number,
                            pattern_code=pattern.code,
                            data={
                                "full_name": patient.user.get_full_name(),
                                "record_number": patient.record_number
                            }
                        )
                    except Exception as sms_error:
                        messages.warning(
                            request,
                            f"بیمار ثبت شد اما ارسال پیامک با خطا مواجه شد: {sms_error}"
                        )

                messages.success(
                    request,
                    f"بیمار «{patient.user.get_full_name()}» با موفقیت ثبت شد."
                )
                return redirect(patient.get_absolute_url())

            except Exception as e:
                messages.error(request, f"خطایی در ذخیره اطلاعات رخ داد: {str(e)}")

    else:
        form = PatientUserForm(initial=initial_data)
        if pending_user:
            form.fields['national_code'].readonly = True
            form.fields['phone_number'].readonly = True

    return render(request, 'patient/patient_form.html', {'form': form, 'pending_user': pending_user})


@login_required
@permission_required("patient.change_patient", raise_exception=True)
def patient_update_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientUserForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات بیمار با موفقیت ویرایش شد.")
            return redirect(patient.get_absolute_url())
    else:
        form = PatientUserForm(instance=patient)

    return render(request, 'patient/patient_form.html', {'form': form, 'patient': patient})


@login_required
@permission_required("patient.view_patient", raise_exception=True)
def patient_list_view(request):
    patients_list = Patient.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(patients_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'patient/patient_list.html', context)


@login_required
@permission_required("patient.view_patient", raise_exception=True)
def patient_detail_view(request, pk):
    patient = get_object_or_404(Patient.objects.select_related('user'), pk=pk)
    return render(request, 'patient/patient_detail.html', {'patient': patient})


@login_required
@permission_required("patient.delete_patient", raise_exception=True)
def patient_delete_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    user = patient.user
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"بیمار '{user.get_full_name()}' و کاربر مرتبط با موفقیت حذف شدند.")
        return redirect(reverse('patient:patient_list'))
    return render(request, 'patient/patient_confirm_delete.html', {'patient': patient})


@login_required
@permission_required("patient.view_patient", raise_exception=True)
def search_patients_api(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__phone_number__icontains=query) |
            Q(user__national_code__icontains=query)
        ).select_related('user')[:10]
        results = [{"id": p.id, "text": f"{p.user.get_full_name()} ({p.user.national_code})"} for p in patients]
    return JsonResponse({"results": results})
