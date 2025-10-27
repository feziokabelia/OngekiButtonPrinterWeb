# check_channels.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ongeki_helper_Web.settings')
django.setup()

from django.conf import settings

print("🔍 检查 Channels 配置:")
print(f"INSTALLED_APPS: {[app for app in settings.INSTALLED_APPS if 'channel' in app.lower()]}")
print(f"ASGI_APPLICATION: {getattr(settings, 'ASGI_APPLICATION', '未设置')}")
print(f"CHANNEL_LAYERS: {getattr(settings, 'CHANNEL_LAYERS', '未设置')}")

try:
    from channels.routing import get_default_application
    app = get_default_application()
    print("✅ ASGI 应用配置正确")
except Exception as e:
    print(f"❌ ASGI 配置错误: {e}")

try:
    from channels.layers import get_channel_layer
    layer = get_channel_layer()
    print("✅ Channel 层配置正确")
except Exception as e:
    print(f"❌ Channel 层错误: {e}")