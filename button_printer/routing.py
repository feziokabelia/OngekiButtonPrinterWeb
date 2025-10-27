from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/hid/$', consumers.HIDConsumer.as_asgi()),
]

print("✅ WebSocket 路由已加载")