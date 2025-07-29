# apps/reception/routing.py

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 👈 اصلاح: استفاده از نام صحیح Consumer و یک URL توصیفی‌تر
    re_path(r"^ws/reception/updates/$", consumers.ReceptionUpdatesConsumer.as_asgi()),
]
