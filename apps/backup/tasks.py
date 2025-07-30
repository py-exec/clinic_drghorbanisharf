from celery import shared_task
from django.conf import settings
from .utils import create_backup, upload_to_cloud
from .models import BackupFile, BackupSettings, StorageProvider
import os
import logging

logger = logging.getLogger("backup")

@shared_task
def scheduled_backup():
    settings_obj = BackupSettings.objects.first()
    include_media = True
    provider = StorageProvider.LOCAL
    password = None
    if settings_obj:
        include_media = settings_obj.include_media
        provider = settings_obj.provider
        if settings_obj.use_encryption:
            password = os.getenv("BACKUP_PASSWORD")
    path = create_backup(include_media=include_media, password=password)
    size = os.path.getsize(path)
    cloud_id = None
    if provider != StorageProvider.LOCAL:
        cloud_id = upload_to_cloud(path, provider)
    BackupFile.objects.create(
        name=os.path.basename(path),
        size=size,
        provider=provider,
        cloud_id=cloud_id,
    )
    logger.info("Scheduled backup created: %s", path)