# apps/reception/status_service.py

from .models import ReceptionServiceStatus, ReceptionService
from django.utils import timezone
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def change_service_status(service_instance, new_status_code, user=None, note=None, duration_seconds=None):
    """
    Changes the status of a ReceptionService and logs the change in ReceptionServiceStatus.
    Also sends a WebSocket update.
    """
    print(f"--- status_service: Attempting to change status for Service ID: {service_instance.id} to {new_status_code} by User: {user} ---") # Added print

    try:
        # Create a new status entry
        ReceptionServiceStatus.objects.create(
            reception_service=service_instance,
            status=new_status_code,
            changed_by=user,
            note=note,
            duration_seconds=duration_seconds,
            timestamp=timezone.now() # Explicitly set timestamp
        )
        print(f"--- status_service: Status changed successfully for Service ID: {service_instance.id} to {new_status_code} ---") # Added print

    except Exception as e:
        print(f"--- status_service: ERROR changing status for Service ID: {service_instance.id}: {e} ---") # Added print
        # You might want to log this error more formally in production

    # The WebSocket message is sent via signals in signals.py, which listens to ReceptionServiceStatus.post_save
    # So, no direct WebSocket send here.