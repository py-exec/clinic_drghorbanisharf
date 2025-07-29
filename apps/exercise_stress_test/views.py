from apps.patient.models import Patient
from apps.prescriptions.models import Prescription
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import StressTestReport


@login_required
def stress_report_detail(request, pk):
    return HttpResponse(f"Stress Test Report Detail #{pk}")


@login_required
def stress_report_update(request, pk):
    return HttpResponse(f"Update Stress Test Report #{pk}")


@login_required
def stress_report_delete(request, pk):
    return HttpResponse(f"Delete Stress Test Report #{pk}")


@login_required
def stress_test_create(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    prescriptions = Prescription.objects.filter(patient=patient).order_by("-created_at")

    if request.method == "POST":
        try:
            StressTestReport.objects.create(
                patient=patient,
                prescription_id=request.POST.get("prescription_id") or None,
                created_by=request.user,

                # شاخص‌های عملکردی
                patient_age=request.POST.get("patient_age"),
                hr_peak_metric=request.POST.get("hr_peak_metric"),
                mets=request.POST.get("mets"),
                sbp_peak_metric=request.POST.get("sbp_peak_metric"),

                # فاز ریکاوری
                recovery_duration=request.POST.get("recovery_duration"),
                hr_recovery=request.POST.get("hr_recovery"),
                sbp_recovery=request.POST.get("sbp_recovery"),
                recovery_st_change=request.POST.get("recovery_st_change"),
                recovery_monitoring=request.POST.get("recovery_monitoring"),
                recovery_symptoms=request.POST.getlist("recovery_symptoms"),

                # پیش تست
                pretest_medications=request.POST.get("pretest_medications"),
                baseline_ecg=request.POST.get("baseline_ecg"),
                pretest_sbp=request.POST.get("pretest_sbp"),
                pretest_dbp=request.POST.get("pretest_dbp"),
                pretest_contra=request.POST.get("pretest_contra"),

                # تست
                stress_type=request.POST.get("stress_type"),
                stress_start_time=request.POST.get("stress_start_time"),
                stress_duration=request.POST.get("stress_duration"),
                stress_stop_reason=request.POST.get("stress_stop_reason"),
                stress_conditions=request.POST.get("stress_conditions"),

                # علائم بالینی
                symptoms=request.POST.getlist("symptoms"),
                hr_rest=request.POST.get("hr_rest"),
                hr_peak=request.POST.get("hr_peak"),
                sbp_rest=request.POST.get("sbp_rest"),
                sbp_peak=request.POST.get("sbp_peak"),
                stress_symptomatic=request.POST.get("stress_symptomatic"),
                borg_scale=request.POST.get("borg_scale"),

                # ECG
                arrhythmia_type=request.POST.get("arrhythmia_type"),
                ecg_leads=request.POST.get("ecg_leads"),
                ecg_changes=request.POST.get("ecg_changes"),

                # اکو
                rwma_severity=request.POST.get("rwma_severity"),
                ef_rest=request.POST.get("ef_rest"),
                ef_post=request.POST.get("ef_post"),
                mr_grade=request.POST.get("mr_grade"),
                rwma_walls=request.POST.get("rwma_walls"),

                # مستندات
                stress_video=request.FILES.get("stress_video"),
                image_saved=request.POST.get("image_saved"),
                technical_issues=request.POST.get("technical_issues"),

                # تحلیل نهایی
                final_comment=request.POST.get("final_comment"),
                final_diagnosis=request.POST.get("final_diagnosis"),
                final_plan=request.POST.get("final_plan"),
            )

            messages.success(request, "✅ تست ورزش با موفقیت ثبت شد.")
            return redirect("stress-test-list")

        except Exception as e:
            messages.error(request, f"❌ خطا در ثبت تست: {e}")

    return render(request, "echo/stress_test_form.html", {
        "patient": patient,
        "prescriptions": prescriptions
    })


@login_required
def stress_test_list(request):
    stress_reports = StressTestReport.objects.select_related("patient", "prescription").order_by("-created_at")
    return render(request, "echo/stress_test_list.html", {
        "reports": stress_reports
    })
