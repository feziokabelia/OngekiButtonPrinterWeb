import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import button_printer.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ongeki_helper_Web.settings')

# 初始化 Django
django.setup()

# 获取 Django 的 ASGI 应用
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(
        button_printer.routing.websocket_urlpatterns
    ),
})