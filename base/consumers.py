import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import User, Room, Message
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Receive message from WebSocket
        data = json.loads(text_data)
        message = data.get('message')
        username = data.get('username')
        room_name = self.room_id
        await self.save_message(username, room_name, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username']
        }))
    @database_sync_to_async
    def save_message(self, username, room, message):
        user = User.objects.get(username=username)
        room = Room.objects.get(id=room)
        return Message.objects.create(user=user, room=room, body=message)
    
class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get room name from the URL
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_name}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Parse the incoming WebSocket message
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        username = text_data_json.get('username')

        if message_type == 'chat_message':
            message = text_data_json.get('message')

            # Broadcast chat message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'username': username,
                    'message': message
                }
            )

        elif message_type == 'code_change':
            code = text_data_json.get('code')

            # Broadcast code change to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'code_change',
                    'username': username,
                    'code': code
                }
            )

    async def chat_message(self, event):
        # Send chat message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'username': event['username'],
            'message': event['message']
        }))

    async def code_change(self, event):
        # Send code change to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'code_change',
            'username': event['username'],
            'code': event['code']
        }))