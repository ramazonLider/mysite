import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from django.contrib.auth.models import User

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
            sender_username = await self.get_sender_username(message.sender_id)
            await self.send(text_data=json.dumps({
                'message': message.content,
                'id': message.id,
                'sender': sender_username
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

        user = self.scope['user']  # Get the current user

        if action == 'update' and message_id:
            await self.update_message(message_id, message_content)
        elif action == 'new':
            await self.save_message(self.room_name, message_content, user)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'id': message_id,
                'action': action,
                'sender': user.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        message_id = event.get('id', None)
        sender = event.get('sender', 'Unknown')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'id': message_id,
            'action': event.get('action', 'new'),
            'sender': sender
        }))

    async def get_last_messages(self, room_name):
        # Fetch the last 10 messages from the database asynchronously
        messages = await database_sync_to_async(
            lambda: list(Message.objects.filter(room_name=room_name).order_by('-timestamp')[:10])
        )()
        return messages

    async def save_message(self, room_name, message_content, user):
        # Save the message to the database asynchronously
        await database_sync_to_async(
            lambda: Message.objects.create(room_name=room_name, content=message_content, sender=user)
        )()

    async def update_message(self, message_id, message_content):
        # Update the message in the database asynchronously
        await database_sync_to_async(
            lambda: Message.objects.filter(id=message_id).update(content=message_content)
        )()

    async def get_sender_username(self, sender_id):
        try:
            # Fetch the sender's username asynchronously
            sender = await database_sync_to_async(
                lambda: User.objects.get(id=sender_id)
            )()
            return sender.username
        except User.DoesNotExist:
            return 'Unknown'
