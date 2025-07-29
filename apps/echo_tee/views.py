from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import TEEEchoReport


@login_required
def tee_report_detail(request, pk):
    return HttpResponse(f"TEE Report Detail #{pk}")


@login_required
def tee_report_update(request, pk):
    return HttpResponse(f"Update TEE Report #{pk}")


@login_required
def tee_report_delete(request, pk):
    return HttpResponse(f"Delete TEE Report #{pk}")


@login_required
def echo_create_tee_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    prescription = Prescription.objects.filter(patient=patient).last()

    if request.method == "POST":
        try:
            if request.POST.get("consent") != "on":
                messages.error(request, "لطفاً تأیید صحت اطلاعات را فعال کنید.")
                return render(request, "echo/tee_echo_form.html", {"patient": patient})

            TEEEchoReport.objects.create(
                patient=patient,
                prescription=prescription,

                history_af=request.POST.get("history_af"),
                history_stroke=request.POST.get("history_stroke"),
                anticoagulant=request.POST.get("anticoagulant"),
                indication=request.POST.get("indication"),

                sedation=request.POST.get("sedation"),
                gag_reflex=request.POST.get("gag_reflex"),
                image_quality=request.POST.get("image_quality"),
                complications=request.POST.get("complications"),

                laa_thrombus=request.POST.get("laa_thrombus"),
                vegetation=request.POST.get("vegetation"),
                pfo=request.POST.get("pfo"),
                prosthetic_motion=request.POST.get("prosthetic_motion"),

                next_step=request.POST.get("next_step"),
                physician_name=request.POST.get("physician_name"),
                exam_date=request.POST.get("exam_date"),
                final_comment=request.POST.get("final_comment"),
                upload_video=request.FILES.get("upload_video"),

                created_by=request.user,
                created_at=timezone.now()
            )

            messages.success(request, "✅ گزارش TEE با موفقیت ثبت شد.")
            return redirect("patient-detail", patient_id=patient.id)

        except Exception as e:
            messages.error(request, f"❌ خطا در ثبت گزارش: {e}")

    return render(request, "echo/tee_echo_form.html", {
        "patient": patient
    })


@login_required
def echo_tee_list(request):
    tee_reports = TEEEchoReport.objects.select_related("patient", "prescription").order_by("-created_at")
    return render(request, "echo/echo_tte_list.html", {
        "reports": tee_reports
    })
