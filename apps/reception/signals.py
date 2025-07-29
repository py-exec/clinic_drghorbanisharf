import re
import logging
from asgiref.sync import async_to_sync
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils.module_loading import import_string
from channels.layers import get_channel_layer
from .models import ReceptionService, ReceptionServiceStatus

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 3600  # 1 hour cache


def sanitize_group_name(name):
    return re.sub(r"[^\w\-.]", "_", name)[:100]  # فقط a-zA-Z0-9-_.


def get_model_for_service_type(service_type):
    if not service_type or not service_type.model_path:
        return None

    cache_key = f"service_model:{service_type.id}"
    model_class = cache.get(cache_key)
    if model_class:
        return model_class

    try:
        model_class = import_string(service_type.model_path)
        cache.set(cache_key, model_class, CACHE_TIMEOUT)
        return model_class
    except Exception as e:
        logger.error(f"[service_model import error] path={service_type.model_path} error={e}")
        return None

@receiver(post_save, sender=ReceptionService)
def create_related_model(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        service_type = instance.tariff.service_type if instance.tariff else None
        model_class = get_model_for_service_type(service_type)
        if not model_class:
            return

        content_type = ContentType.objects.get_for_model(instance)
        record, created = model_class.objects.get_or_create(
            content_type=content_type,
            object_id=instance.id,
            defaults={
                'patient': instance.reception.patient,
                'created_by': instance.created_by,
            }
        )
        if created:
            logger.info(f"✅ رکورد {model_class.__name__} برای خدمت {instance.id} ایجاد شد.")
        else:
            logger.info(f"⚠️ رکورد {model_class.__name__} برای خدمت {instance.id} از قبل وجود داشت.")
    except Exception as e:
        logger.exception(f"❌ [ایجاد رکورد تخصصی] service_id={instance.id} | خطا: {e}")

def send_reception_ws_event(instance, action):
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        service_type = instance.tariff.service_type if instance.tariff else None
        if not service_type or not service_type.updates_enabled or not service_type.assigned_role:
            return

        role_code = service_type.assigned_role.code
        group_name = sanitize_group_name(f"role_{role_code}")

        last_status = instance.status
        status_display = dict(ReceptionServiceStatus.STATUS_CHOICES).get(last_status, "نامشخص")

        payload = {
            "type": "reception_update",  # باید با متدی در consumer یکی باشه
            "action": action,
            "service": {
                "id": instance.id,
                "reception_id": instance.reception.id,
                "service_name": service_type.name,
                "service_type": service_type.code,
                "status": last_status,
                "status_display": status_display,
                "tracking_code": instance.tracking_code,
                "created_at": instance.created_at.isoformat(),
                "scheduled_time": instance.scheduled_time.isoformat() if instance.scheduled_time else None,
                "estimated_duration": str(instance.estimated_duration) if instance.estimated_duration else None,
                "done_at": instance.done_at.isoformat() if instance.done_at else None,
                "cancelled_at": instance.cancelled_at.isoformat() if instance.cancelled_at else None,
            }
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            payload
        )

    except Exception as e:
        logger.exception(f"❌ [ارسال WebSocket] service_id={instance.id} | خطا: {e}")

@receiver(post_save, sender=ReceptionService)
def notify_service_create_or_update(sender, instance, created, **kwargs):
    try:
        send_reception_ws_event(instance, "created" if created else "updated")
    except Exception as e:
        logger.error(f"[notify_service_create_or_update] ❌ {e}")

@receiver(post_delete, sender=ReceptionService)
def notify_service_delete(sender, instance, **kwargs):
    try:
        send_reception_ws_event(instance, "deleted")
    except Exception as e:
        logger.error(f"[notify_service_delete] ❌ {e}")

@receiver(post_save, sender=ReceptionServiceStatus)
def notify_status_change(sender, instance, created, **kwargs):
    try:
        send_reception_ws_event(instance.reception_service, "status_changed")
    except Exception as e:
        logger.error(f"[notify_status_change] ❌ {e}")
