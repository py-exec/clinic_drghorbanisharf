# clinic_drghorbanisharif/routing.py

from django.urls import re_path
from apps.reception.consumers import ReceptionUpdatesConsumer

websocket_urlpatterns = [
    re_path(r'ws/reception/updates/$', ReceptionUpdatesConsumer.as_asgi()),
]
