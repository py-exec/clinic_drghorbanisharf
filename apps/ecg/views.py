from .models import ECGRecord
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.template.loader import render_to_string
from django.http import JsonResponse

@login_required
def ecg_table_partial(request):
    reports = ECGRecord.objects.select_related("patient").order_by("-created_at")
    html = render_to_string("ecg/partials/_ecg_table.html", {"reports": reports})
    return JsonResponse({"html": html})


@login_required
def ecg_report_list(request):
    ecg_reports = ECGRecord.objects.select_related("patient", "prescription").order_by("-created_at")
    return render(request, "ecg/ecg_list.html", {
        "reports": ecg_reports
    })


@login_required
def ecg_create_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    prescriptions = Prescription.objects.filter(patient=patient).order_by("-created_at")

    if request.method == "POST":
        try:
            ecg = ECGRecord.objects.create(
                patient=patient,
                prescription_id=request.POST.get("prescription_id") or None,
                ref_doctor=request.POST.get("ref_doctor"),
                ref_mcn=request.POST.get("ref_mcn"),
                ecg_reason=request.POST.get("ecg_reason"),
                cardiac_history=request.POST.get("cardiac_history"),

                ecg_type=request.POST.get("ecg_type"),
                patient_position=request.POST.get("patient_position"),
                room_temp=request.POST.get("room_temp"),
                ecg_location=request.POST.get("ecg_location"),
                ecg_quality=request.POST.get("ecg_quality"),
                tech_issue=request.POST.get("tech_issue") == "on",
                issue_desc=request.POST.get("issue_desc"),
                device_serial=request.POST.get("device_serial"),
                start_time=request.POST.get("start_time"),
                end_time=request.POST.get("end_time"),

                hr=request.POST.get("hr"),
                rhythm=request.POST.get("rhythm"),
                axis=request.POST.get("axis"),
                qrs=request.POST.get("qrs"),
                qtc=request.POST.get("qtc"),
                p_wave=request.POST.get("p_wave"),
                st_t=request.POST.get("st_t"),
                q_wave=request.POST.get("q_wave") == "on",
                u_wave=request.POST.get("u_wave") == "on",
                tech_opinion=request.POST.get("tech_opinion"),

                ecg_repeat=request.POST.get("ecg_repeat") == "on",
                repeat_reason=request.POST.get("repeat_reason"),
                tech_signature=request.POST.get("tech_signature"),
                doctor_signature=request.POST.get("doctor_signature"),
                ecg_file=request.FILES.get("ecg_file"),
                created_by=request.user
            )

            messages.success(request, f"✅ ECG برای بیمار «{patient.full_name}» با موفقیت ثبت شد.")
            return redirect("ecg-report-list")

        except Exception as e:
            messages.error(request, f"❌ خطا در ثبت ECG: {e}")

    return render(request, "ecg/ecg_create.html", {
        "patient": patient,
        "prescriptions": prescriptions
    })


@login_required
def ecg_report_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    report = ECGRecord.objects.filter(patient=patient).order_by("-created_at").first()
    if not report:
        messages.warning(request, "هیچ گزارشی برای این بیمار ثبت نشده است.")
        return redirect("ecg-report-list")

    return render(request, "clinic_services/ecg/ecg_detail.html", {
        "report": report,
        "patient": patient
    })


@login_required
def ecg_report_update(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    report = ECGRecord.objects.filter(patient=patient).order_by("-created_at").first()
    prescriptions = Prescription.objects.filter(patient=patient).order_by("-created_at")

    if not report:
        messages.warning(request, "گزارشی برای ویرایش یافت نشد.")
        return redirect("ecg-report-list")

    if request.method == "POST":
        try:
            report.prescription_id = request.POST.get("prescription_id") or None
            report.ref_doctor = request.POST.get("ref_doctor")
            report.ref_mcn = request.POST.get("ref_mcn")
            report.ecg_reason = request.POST.get("ecg_reason")
            report.cardiac_history = request.POST.get("cardiac_history")

            report.ecg_type = request.POST.get("ecg_type")
            report.patient_position = request.POST.get("patient_position")
            report.room_temp = request.POST.get("room_temp")
            report.ecg_location = request.POST.get("ecg_location")
            report.ecg_quality = request.POST.get("ecg_quality")
            report.tech_issue = request.POST.get("tech_issue") == "on"
            report.issue_desc = request.POST.get("issue_desc")
            report.device_serial = request.POST.get("device_serial")
            report.start_time = request.POST.get("start_time")
            report.end_time = request.POST.get("end_time")

            report.hr = request.POST.get("hr")
            report.rhythm = request.POST.get("rhythm")
            report.axis = request.POST.get("axis")
            report.qrs = request.POST.get("qrs")
            report.qtc = request.POST.get("qtc")
            report.p_wave = request.POST.get("p_wave")
            report.st_t = request.POST.get("st_t")
            report.q_wave = request.POST.get("q_wave") == "on"
            report.u_wave = request.POST.get("u_wave") == "on"
            report.tech_opinion = request.POST.get("tech_opinion")

            report.ecg_repeat = request.POST.get("ecg_repeat") == "on"
            report.repeat_reason = request.POST.get("repeat_reason")
            report.tech_signature = request.POST.get("tech_signature")
            report.doctor_signature = request.POST.get("doctor_signature")

            if request.FILES.get("ecg_file"):
                report.ecg_file = request.FILES.get("ecg_file")

            report.save()
            messages.success(request, "✅ ویرایش گزارش با موفقیت انجام شد.")
            return redirect("ecg-detail", patient_id=patient.id)

        except Exception as e:
            messages.error(request, f"❌ خطا در ویرایش گزارش: {e}")

    return render(request, "clinic_services/ecg/ecg_edit.html", {
        "report": report,
        "patient": patient,
        "prescriptions": prescriptions
    })


@login_required
def ecg_report_delete(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    report = ECGRecord.objects.filter(patient=patient).order_by("-created_at").first()

    if not report:
        messages.warning(request, "هیچ گزارشی برای حذف وجود ندارد.")
        return redirect("ecg-report-list")

    if request.method == "POST":
        report.delete()
        messages.success(request, "گزارش با موفقیت حذف شد.")
        return redirect("ecg-report-list")

    return render(request, "clinic_services/ecg/ecg_confirm_delete.html", {
        "report": report,
        "patient": patient
    })