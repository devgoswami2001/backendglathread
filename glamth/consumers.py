import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]

        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.room = f"chat_{self.thread_id}"
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
