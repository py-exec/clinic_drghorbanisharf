from django.http import HttpResponse
from django.shortcuts import render


# [GET] - لیست همه پروسیجرها
def procedure_list(request):
    return HttpResponse("Procedure List")


# [GET, POST] - ایجاد پروسیجر برای یک بیمار خاص
def procedure_create(request, patient_id):
    return HttpResponse(f"Create Procedure for Patient #{patient_id}")


# [GET] - جزئیات یک پروسیجر خاص
def procedure_detail(request, pk):
    return HttpResponse(f"Procedure Detail View for Procedure #{pk}")


# [GET, POST] - ویرایش پروسیجر خاص
def procedure_update(request, pk):
    return HttpResponse(f"Update Procedure #{pk}")


# [POST] - حذف پروسیجر
def procedure_delete(request, pk):
    return HttpResponse(f"Delete Procedure #{pk}")
