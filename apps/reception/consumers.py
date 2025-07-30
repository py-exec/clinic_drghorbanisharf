# apps/reception/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ReceptionUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'reception_updates'

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        print(f"--- Consumer: WebSocket connected. Channel: {self.channel_name}, Group: {self.group_name} ---") # Added print
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"--- Consumer: WebSocket disconnected. Channel: {self.channel_name}, Close code: {close_code} ---") # Added print

    async def receive(self, text_data):
        # This consumer only sends messages, it does not expect to receive from client
        pass

    async def service_message(self, event):
        message = event['message_type']
        service = event['service']
        stats = event.get('stats', {}) # Get stats, default to empty dict if not present

        print(f"--- Consumer: Received message of type '{message}' for Service ID: {service.get('id')} ---") # Added print
        print(f"--- Consumer: Service Data: {service} ---") # Added print
        print(f"--- Consumer: Stats Data: {stats} ---") # Added print

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message_type': message,
            'service': service,
            'stats': stats,
            'action': 'update' # Consider if you need more dynamic actions here
        }))
        print(f"--- Consumer: Message sent to frontend. ---") # Added print