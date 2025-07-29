# apps/reception/consumers.py
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ReceptionUpdatesConsumer(AsyncWebsocketConsumer):
    """
    این Consumer مسئول اطلاع‌رسانی لحظه‌ای تغییرات در خدمات پذیرش است.
    """

    async def connect(self):
        self.user = self.scope["user"]

        # ⛔ فقط کاربران لاگین کرده
        if not self.user.is_authenticated:
            await self.close()
            return

        # ⛔ فقط با پرمیشن مناسب
        has_perm = await self.check_user_permission(self.user, "reception.view_reception")
        if not has_perm:
            await self.close()
            return

        # 🧠 تعیین گروه WebSocket بر اساس نقش کاربر
        role = await self.get_user_role(self.user)
        if not role:
            await self.close()
            return

        self.group_name = f"role_{role.code}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def reception_update(self, event):
        """
        متد دریافت پیام از گروه و ارسال به کلاینت WebSocket.
        """
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def check_user_permission(self, user, perm_code):
        return user.has_perm(perm_code)

    @database_sync_to_async
    def get_user_role(self, user):
        """
        نقش اصلی کاربر را برمی‌گرداند.
        """
        return getattr(user, "role", None)  # اگر چند نقش داری، اینجا رو تغییر بده
