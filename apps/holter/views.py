# apps/holter/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from apps.holter.models import HolterDevice, HolterInstallation, HolterRepairLog, HolterStatus, HolterStatusLog




@login_required
def holter_installation_form(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    available_devices = HolterDevice.objects.filter(status=HolterStatus.READY, is_active=True)
    prescriptions = Prescription.objects.filter(patient=patient)

    if request.method == "POST":
        try:
            device = get_object_or_404(HolterDevice, pk=request.POST.get("device_id"))
            prescription = get_object_or_404(Prescription, pk=request.POST.get("prescription_id"))

            installation = HolterInstallation.objects.create(
                patient=patient,
                device=device,
                doctor_order=prescription,

                clinic_section=request.POST.get("clinic_section"),
                internal_ref_code=request.POST.get("internal_ref_code"),

                holter_type=request.POST.get("holter_type"),
                doctor_name=request.POST.get("doctor_name"),
                order_datetime=request.POST.get("order_datetime"),
                needed_duration=request.POST.get("needed_duration"),
                preliminary_diagnosis=request.POST.get("preliminary_diagnosis"),
                allergy_to_gel=request.POST.get("allergy_to_gel") == "دارد",
                patient_symptoms=request.POST.get("patient_symptoms"),

                install_datetime=request.POST.get("install_datetime"),
                technician_name=request.POST.get("technician_name"),
                skin_status=request.POST.get("skin_status"),
                install_location=request.POST.get("install_location"),
                body_temp=request.POST.get("body_temp"),
                patient_position=request.POST.get("patient_position"),
                ecg_cable_type=request.POST.get("ecg_cable_type"),
                battery_percent=request.POST.get("battery_percent"),
                battery_expiry=request.POST.get("battery_expiry"),
                serial_number=request.POST.get("serial_number"),
                qr_code=request.POST.get("qr_code"),
                is_calibrated=request.POST.get("is_calibrated") == "بله",
                initial_signal_status=request.POST.get("initial_signal_status"),
                initial_test_result=request.POST.get("initial_test_result"),

                device_model=request.POST.get("device_model"),
                device_brand=request.POST.get("device_brand"),
                ecg_cable_brand=request.POST.get("ecg_cable_brand"),
                electrode_count=request.POST.get("electrode_count"),
                electrode_brand=request.POST.get("electrode_brand"),
                electrode_expiry=request.POST.get("electrode_expiry"),
                extra_battery_given=request.POST.get("extra_battery_given") == "بله",
                extra_battery_expiry=request.POST.get("extra_battery_expiry"),
                reusable_parts=request.POST.get("reusable_parts") == "بله",
                seal_status=request.POST.get("seal_status"),

                brochure_given=request.POST.get("brochure_given") == "بله",
                device_care_taught=request.POST.get("device_care_taught") == "بله",
                patient_understood=request.POST.get("patient_understood") == "بله",
                emergency_contact_given=request.POST.get("emergency_contact_given") == "بله",
                patient_signature=request.POST.get("patient_signature"),

                device_on=request.POST.get("device_on") == "بله",
                signal_visible=request.POST.get("signal_visible") == "بله",
                battery_sufficient=request.POST.get("battery_sufficient") == "بله",
                cables_connected=request.POST.get("cables_connected") == "بله",
                error_code=request.POST.get("error_code"),
                final_note=request.POST.get("final_note"),

                created_by=request.user,
                created_at=timezone.now()
            )

            device.status = HolterStatus.ASSIGNED_TO_PATIENT
            device.patient = patient
            device.status_updated_at = timezone.now()
            device.save()

            messages.success(request, "✅ نصب هولتر با موفقیت ثبت شد.")
            return redirect("holter-detail", device_id=device.id)

        except Exception as e:
            messages.error(request, f"❌ خطا در ثبت اطلاعات: {e}")

    return render(request, "holter/Installation_Holter.html", {
        "patient": patient,
        "available_devices": available_devices,
        "prescriptions": prescriptions
    })


# 📍 لیست همه دستگاه‌ها
@login_required
def holter_list(request):
    devices = HolterDevice.objects.all()
    return render(request, "holter/holter_list.html", {"devices": devices})


# 📍 ساخت دستگاه جدید
@login_required
def holter_create(request):
    if request.method == "POST":
        try:
            HolterDevice.objects.create(
                inventory_item_id=request.POST.get("inventory_item"),
                serial_number=request.POST.get("serial_number"),
                asset_code=request.POST.get("asset_code"),
                internal_code=request.POST.get("internal_code"),
                model_name=request.POST.get("model_name"),
                device_type=request.POST.get("device_type"),
                firmware_version=request.POST.get("firmware_version"),
                battery_status=request.POST.get("battery_status"),
                is_calibrated=request.POST.get("is_calibrated") == "true",
                is_active=request.POST.get("is_active") == "true",
                created_by=request.user
            )
            messages.success(request, "✅ دستگاه با موفقیت ثبت شد.")
            return redirect("holter:holter-device-list")
        except Exception as e:
            messages.error(request, f"❌ خطا: {e}")

    return render(request, "holter/holter_create.html")


# 📍 مشاهده جزئیات دستگاه
@login_required
def holter_detail(request, device_id):
    device = get_object_or_404(HolterDevice, pk=device_id)
    return render(request, "holter/holter_detail.html", {"device": device})


# 📍 حذف دستگاه
@login_required
def holter_delete(request, device_id):
    device = get_object_or_404(HolterDevice, pk=device_id)

    if request.method == "POST":
        device.delete()
        messages.success(request, "✅ دستگاه حذف شد.")
        return redirect("holter-list")

    return render(request, "holter/confirm_delete.html", {"device": device})


# 📍 تغییر وضعیت دستگاه
@login_required
def holter_change_status(request, device_id):
    device = get_object_or_404(HolterDevice, pk=device_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in HolterStatus.values:
            old_status = device.status
            device.status = new_status
            device.status_updated_at = timezone.now()
            device.save()

            HolterStatusLog.objects.create(
                device=device,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user
            )
            messages.success(request, "✅ وضعیت دستگاه به‌روزرسانی شد.")
        else:
            messages.error(request, "❌ وضعیت وارد شده نامعتبر است.")

    return redirect("holter-detail", device_id=device.id)


# 📍 فرم تحویل یا دریافت دستگاه (نمایش فقط)
@login_required
def holter_receive_form(request):
    return render(request, "holter/Receive_Holter.html")


# 📍 ثبت تعمیر دستگاه
@login_required
def holter_repair_log(request, device_id):
    device = get_object_or_404(HolterDevice, pk=device_id)

    if request.method == "POST":
        try:
            HolterRepairLog.objects.create(
                device=device,
                issue_description=request.POST.get("issue_description"),
                repair_start=request.POST.get("repair_start"),
                repair_end=request.POST.get("repair_end"),
                cost=request.POST.get("cost"),
                repaired_by=request.POST.get("repaired_by"),
                resolution_notes=request.POST.get("resolution_notes"),
                created_by=request.user
            )

            device.status = HolterStatus.UNDER_REPAIR
            device.status_updated_at = timezone.now()
            device.save()

            HolterStatusLog.objects.create(
                device=device,
                old_status=device.status,
                new_status=HolterStatus.UNDER_REPAIR,
                changed_by=request.user
            )

            messages.success(request, "✅ گزارش تعمیر ثبت شد.")
            return redirect("holter-detail", device_id=device.id)

        except Exception as e:
            messages.error(request, f"❌ خطا در ثبت تعمیر: {e}")

    return render(request, "holter/repair_form.html", {"device": device})