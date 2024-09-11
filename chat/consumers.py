from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Message  # Assuming you have a Message model to store messages

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        # Fetch and send the last messages when a user connects
        messages = await self.get_last_messages(self.room_name)
        for message in messages:
            await self.send(text_data=json.dumps({
                'message': message.content,
                'id': message.id  # Send the message ID to update it later
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')
        message_id = data.get('id')
        action = data.get('action')

        if action == 'update' and message_id:
            # Update the message in the database
            await self.update_message(message_id, message_content)

        else:
            # Save the new message to the database
            await self.save_message(self.room_name, message_content)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'id': message_id,
                'action': action
            }
        )

    async def chat_message(self, event):
        message = event['message']
        message_id = event.get('id', None)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'id': message_id,
            'action': event.get('action', 'new')  # Action type: 'new' or 'update'
        }))

    async def get_last_messages(self, room_name):
        # Fetch the last 10 messages from the database asynchronously
        messages = await database_sync_to_async(
            lambda: list(Message.objects.filter(room_name=room_name).order_by('-timestamp')[:10])
        )()
        return messages

    async def save_message(self, room_name, message_content):
        # Save the message to the database asynchronously
        await database_sync_to_async(
            lambda: Message.objects.create(room_name=room_name, content=message_content)
        )()

    async def update_message(self, message_id, message_content):
        # Update the message in the database asynchronously
        await database_sync_to_async(
            lambda: Message.objects.filter(id=message_id).update(content=message_content)
        )()
