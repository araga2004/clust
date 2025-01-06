from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/room/(?P<room_id>\d+)', 
        consumers.ChatConsumer.as_asgi()
    ),
    re_path(
        r'ws/room-code/(?P<room_id>\d+)', 
        consumers.RoomConsumer.as_asgi()
    ),
]