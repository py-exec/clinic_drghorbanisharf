import re
import logging
from asgiref.sync import async_to_sync
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils.module_loading import import_string
from channels.layers import get_channel_layer
from django.db.models import Subquery, OuterRef
from django.db.models.expressions import Exists
from django.apps import apps
from django.utils import timezone
from django.db.models.fields.reverse_related import OneToOneRel, ManyToOneRel  # For inspecting relationships

from .models import ReceptionService, ReceptionServiceStatus, ServiceType

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 3600  # 1 hour cache


def sanitize_group_name(name):
    """Sanitizes group names for Channels."""
    return re.sub(r"[^\w\-.]", "_", name)[:100]


def get_model_from_path(model_path):
    """Dynamically imports and caches a model class from a full path."""
    if not model_path:
        return None

    cache_key = f"model_from_path:{model_path}"
    model_class = cache.get(cache_key)
    if model_class:
        logger.debug(f"[get_model_from_path] Cache hit for {model_path}")
        return model_class

    try:
        model_class = import_string(model_path)
        cache.set(cache_key, model_class, CACHE_TIMEOUT)
        logger.info(f"[get_model_from_path] Successfully imported and cached {model_path}")
        return model_class
    except Exception as e:
        logger.error(f"[get_model_from_path Error] path={model_path} error={e}")
        return None


def get_stage_model_info(base_model_class):
    """
    Dynamically identifies related 'stage' models and their ForeignKey names
    based on the base model class. This relies on your app's naming conventions.
    Returns a dict like {'reception': {'model_name': 'HolterHRReception', 'fk_field': 'installation'}, ...}
    """
    stage_info = {}

    # Iterate through all reverse relationships of the base model
    # This finds models that have a ForeignKey pointing back to base_model_class
    for rel in base_model_class._meta.get_all_related_objects():
        # Check if it's a ManyToOneRel (ForeignKey on the other side) or OneToOneRel
        if isinstance(rel, (ManyToOneRel, OneToOneRel)):
            related_model = rel.related_model
            fk_field_name = rel.field.name  # The name of the ForeignKey field on the related model

            # Check common stage model suffixes and assign a generic stage name
            if 'Reception' in related_model.__name__:
                stage_info['reception'] = {'model_name': related_model.__name__, 'fk_field': fk_field_name}
            elif 'Reading' in related_model.__name__:
                stage_info['reading'] = {'model_name': related_model.__name__, 'fk_field': fk_field_name}
            elif 'Report' in related_model.__name__:
                stage_info['report'] = {'model_name': related_model.__name__, 'fk_field': fk_field_name}
            # Add other common stage names/suffixes if you have them

    return stage_info


def check_specialized_record_existence(service_instance):
    """
    Checks for the existence of specialized records (base and stages) for a given ReceptionService dynamically.
    Returns a dictionary of boolean flags and specialized IDs. This function is now fully generic.
    """
    flags = {
        'has_specialized_record': False,
        'specialized_base_id': None,  # Changed from installation_id to be more generic
        'has_stage_reception': False,
        'has_stage_reading': False,
        'has_stage_report': False,  # For services with a single final report model like Tilt
        'is_multi_stage_service': False,
    }

    service_type = service_instance.tariff.service_type if service_instance.tariff else None
    if not service_type or not service_type.model_path:
        return flags

    SpecializedBaseModel = get_model_from_path(service_type.model_path)
    if not SpecializedBaseModel:
        return flags

    # Check for the existence of the base specialized record
    base_record_qs = SpecializedBaseModel.objects.filter(
        content_type=ContentType.objects.get_for_model(ReceptionService),
        object_id=service_instance.pk
    )

    if base_record_qs.exists():
        flags['has_specialized_record'] = True
        base_record_instance = base_record_qs.first()
        flags['specialized_base_id'] = base_record_instance.pk

        # Dynamically identify and check for stage models using _meta inspection
        stage_models_info = get_stage_model_info(SpecializedBaseModel)

        if stage_models_info:
            flags['is_multi_stage_service'] = True

            for stage_name, info in stage_models_info.items():
                try:
                    StageModelClass = apps.get_model(SpecializedBaseModel._meta.app_label, info['model_name'])
                    # Filter based on the dynamically discovered ForeignKey field name
                    filter_kwargs = {info['fk_field']: base_record_instance}
                    if StageModelClass.objects.filter(**filter_kwargs).exists():
                        if stage_name == 'reception':
                            flags['has_stage_reception'] = True
                        elif stage_name == 'reading':
                            flags['has_stage_reading'] = True
                        elif stage_name == 'report':  # This could be a stage too, depending on definition
                            flags['has_stage_report'] = True
                except LookupError:  # Model not found
                    continue
                except Exception as e:
                    logger.warning(
                        f"Error checking stage model {info['model_name']} for service {service_instance.id}: {e}")
        else:  # If no stage models are found, it's a single-stage service (like a direct report)
            flags['is_multi_stage_service'] = False
            # If a base specialized record exists for a single-stage service, then its 'report' exists
            flags['has_stage_report'] = True  # This handles cases like TiltTestReport directly being the 'report'

    return flags


# IMPORTANT: The calculate_dashboard_stats function is REMOVED from signals.py.
# Dashboard stats (especially for multi-stage queues like Holter HR) should be calculated
# in the relevant views.py (e.g., apps/holter_hr/views.py) or via dedicated API endpoints.
# This keeps signals.py fully generic.


def send_reception_ws_event(reception_service_instance, message_type, action=None):
    """
    Sends a WebSocket event for ReceptionService updates.
    Includes comprehensive service data and dynamically calculated stage flags.
    Does NOT include dashboard stats for specific queues, as that logic is now external.
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer not available. WebSocket message NOT sent.")
            return

        service_type = getattr(reception_service_instance.tariff, "service_type", None)
        if not service_type or not service_type.assigned_role:
            logger.debug(f"ServiceType not eligible for WS updates. Service ID: {reception_service_instance.id}")
            return

        group_name = 'reception_updates'

        current_status_code = reception_service_instance.status
        current_status_display = dict(reception_service_instance.status_history.model.STATUS_CHOICES).get(
            current_status_code, "نامشخص")

        # Prepare basic service data payload
        service_data = {
            "id": reception_service_instance.id,
            "reception_id": reception_service_instance.reception.id,
            "reception_code": reception_service_instance.reception.admission_code,
            "patient_name": str(reception_service_instance.reception.patient),
            "service_type_code": service_type.code,  # Using service_type_code for clarity
            "service_name": service_type.name,
            "created_at": reception_service_instance.created_at.isoformat(),
            "status_code": current_status_code,
            "status_display": current_status_display,
            "tracking_code": reception_service_instance.tracking_code,
            "scheduled_time": reception_service_instance.scheduled_time.isoformat() if reception_service_instance.scheduled_time else None,
            "estimated_duration": str(
                reception_service_instance.estimated_duration) if reception_service_instance.estimated_duration else None,
            "done_at": reception_service_instance.done_at.isoformat() if reception_service_instance.done_at else None,
            "cancelled_at": reception_service_instance.cancelled_at.isoformat() if reception_service_instance.cancelled_at else None,
        }

        # Dynamically add specialized record existence flags
        service_flags = check_specialized_record_existence(reception_service_instance)
        service_data.update(service_flags)  # Merge flags into service_data

        # Dashboard stats are NO LONGER calculated here.
        # The frontend (or a dedicated API) will request these when needed.
        # This keeps the signal handler generic and efficient.

        payload = {
            "type": "service_message",
            "message_type": message_type,
            "action": action,
            "service": service_data,
            # "stats": stats_data, # REMOVED: Dashboard stats are not sent from here
        }

        async_to_sync(channel_layer.group_send)(group_name, payload)
        logger.info(
            f"📡 WebSocket sent for service #{reception_service_instance.id} (Type: {message_type}) to group {group_name}")

    except Exception as e:
        logger.exception(
            f"❌ [send_reception_ws_event Error] service_id={reception_service_instance.id if reception_service_instance else 'N/A'} | {e}")


# Signal for ReceptionService creation
@receiver(post_save, sender=ReceptionService)
def handle_reception_service_save(sender, instance, created, **kwargs):
    """
    Handles initial status creation for new ReceptionServices
    and sends a WebSocket update.
    """
    if created:
        logger.info(f"✅ ReceptionService created: {instance.id}. Ensuring 'pending' status.")
        if not ReceptionServiceStatus.objects.filter(reception_service=instance, status='pending').exists():
            ReceptionServiceStatus.objects.create(
                reception_service=instance,
                status='pending',
                changed_by=instance.created_by,
                timestamp=timezone.now()
            )
            logger.info(f"Initial 'pending' status created for ReceptionService ID: {instance.id}.")
        send_reception_ws_event(instance, "service_created", "created")
    logger.debug(f"ReceptionService save signal - created={created} for service {instance.id}")


# Signal for any change in ReceptionServiceStatus
@receiver(post_save, sender=ReceptionServiceStatus)
def handle_reception_service_status_change(sender, instance, created, **kwargs):
    """
    Sends WebSocket update whenever a ReceptionServiceStatus record is saved (created or updated).
    This is the primary trigger for live updates based on status changes.
    """
    logger.info(
        f"🔄 ReceptionServiceStatus changed/created for Service ID: {instance.reception_service.id} to status: {instance.status}. Triggering WebSocket update.")
    send_reception_ws_event(instance.reception_service, "status_changed", "updated")


# Signal for ReceptionService deletion
@receiver(post_delete, sender=ReceptionService)
def handle_reception_service_delete(sender, instance, **kwargs):
    """
    Sends WebSocket update when a ReceptionService is deleted.
    """
    logger.info(f"🗑️ ReceptionService deleted: {instance.id}.")
    send_reception_ws_event(instance, "service_deleted", "deleted")