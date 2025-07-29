from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import TTEEchoReport


@login_required
def tte_report_detail(request, pk):
    return HttpResponse(f"TTE Report Detail #{pk}")


@login_required
def tte_report_update(request, pk):
    return HttpResponse(f"Update TTE Report #{pk}")


@login_required
def tte_report_delete(request, pk):
    return HttpResponse(f"Delete TTE Report #{pk}")


@login_required
def echo_create_tte_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    prescriptions = Prescription.objects.filter(patient=patient).order_by("-created_at")

    if request.method == "POST":
        try:
            TTEEchoReport.objects.create(
                patient=patient,
                prescription_id=request.POST.get("prescription_id") or None,
                exam_datetime=request.POST.get("exam_datetime") or timezone.now(),

                ef=request.POST.get("ef"),
                lv_dysfunction=request.POST.get("lv_dysfunction"),
                lvedd=request.POST.get("lvedd"),
                lvesd=request.POST.get("lvesd"),
                gls=request.POST.get("gls"),
                image_type=request.POST.get("image_type"),

                tapse=request.POST.get("tapse"),
                spap=request.POST.get("spap"),
                ivc_status=request.POST.get("ivc_status"),

                mitral_type=request.POST.get("mitral_type"),
                mitral_severity=request.POST.get("mitral_severity"),
                mitral_features=request.POST.get("mitral_features"),

                aortic_type=request.POST.get("aortic_type"),
                aortic_severity=request.POST.get("aortic_severity"),
                aortic_features=request.POST.get("aortic_features"),

                tricuspid_type=request.POST.get("tricuspid_type"),
                tricuspid_severity=request.POST.get("tricuspid_severity"),

                pulmonary_type=request.POST.get("pulmonary_type"),
                pulmonary_severity=request.POST.get("pulmonary_severity"),

                pericardial_effusion=request.POST.get("pericardial_effusion"),
                pleural_effusion=request.POST.get("pleural_effusion"),
                mass_or_clot=request.POST.get("mass_or_clot"),
                aneurysm=request.POST.get("aneurysm"),

                image_quality=request.POST.get("image_quality"),
                image_limitation_reason=request.POST.get("image_limitation_reason"),
                probe_type=request.POST.get("probe_type"),
                ecg_sync=request.POST.get("ecg_sync") == "بله",

                patient_cooperation=request.POST.get("patient_cooperation") == "بله",
                all_views_taken=request.POST.get("all_views_taken") == "بله",
                technician_name=request.POST.get("technician_name"),
                technician_note=request.POST.get("technician_note"),

                need_advanced_echo=request.POST.get("need_advanced_echo"),
                reason_advanced_echo=request.POST.get("reason_advanced_echo"),
                final_report=request.POST.get("final_report"),
                report_date=request.POST.get("report_date"),
                reporting_physician=request.POST.get("reporting_physician"),

                upload_file=request.FILES.get("upload_file"),
                created_by=request.user,
            )
            messages.success(request, "✅ گزارش اکو معمولی (TTE) با موفقیت ثبت شد.")
            return redirect("echo-tte-list")

        except Exception as e:
            messages.error(request, f"❌ خطا در ثبت گزارش: {e}")

    return render(request, "echo/tte_echo_form.html", {
        "patient": patient,
        "prescriptions": prescriptions
    })


@login_required
def echo_tte_list(request):
    tte_reports = TTEEchoReport.objects.select_related("patient", "prescription").order_by("-created_at")
    return render(request, "echo/echo_tte_list.html", {
        "reports": tte_reports
    })
