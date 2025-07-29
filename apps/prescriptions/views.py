from apps.patient.models import Patient
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .models import Prescription


@login_required
def doctor_review_list(request):
    prescriptions = Prescription.objects.exclude(final_doctor_note__isnull=True).select_related("patient",
                                                                                                "doctor").order_by(
        "-created_at")
    return render(request, "prescriptions/doctor_review_list.html", {
        "prescriptions": prescriptions
    })


@login_required
def doctor_review_create(request, patient_id):
    return HttpResponse(f"Create doctor review for patient #{patient_id}")


@login_required
def doctor_review_detail(request, pk):
    return HttpResponse(f"Doctor review detail for prescription #{pk}")


@login_required
def doctor_review_update(request, pk):
    return HttpResponse(f"Update doctor review #{pk}")


@login_required
def doctor_review_delete(request, pk):
    return HttpResponse(f"Delete doctor review #{pk}")
