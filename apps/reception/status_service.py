# apps/reception/status_service.py

from apps.reception.models import ReceptionServiceStatus


def change_service_status(service, new_status, user=None, note=None):
    last_status = service.status
    if last_status == new_status:
        return False

    ReceptionServiceStatus.objects.create(
        reception_service=service,
        status=new_status,
        changed_by=user,
        note=note
    )
    return True
