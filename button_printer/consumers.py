# button_printer/consumers.py
import json
import asyncio
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from .services import HIDService


class HIDConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_type = None
        self.device_id = None
        self.connected_time = None

    async def connect(self):
        """WebSocket连接建立 - 优化版本"""
        self.connected_time = time.time()

        await self.accept()

        # 立即发送性能模式确认
        await self.send_immediately({
            'type': 'performance_mode',
            'enabled': True,
            'timestamp': self.connected_time
        })

        # 快速确定客户端类型
        query_string = self.scope.get('query_string', b'').decode()
        if 'client_type=hid_reader' in query_string:
            self.client_type = 'hid_reader'
            self.device_id = self.get_device_id_from_query(query_string)
        else:
            self.client_type = 'web_client'

        # 加入广播组
        await self.channel_layer.group_add("web_clients", self.channel_name)

        # 快速发送连接确认
        await self.send_immediately({
            'type': 'connection_established',
            'client_type': self.client_type,
            'message': '连接已建立',
            'high_performance': True,
            'timestamp': self.connected_time
        })

        print(f"✅ {self.client_type} 连接: {self.channel_name}")

    def get_device_id_from_query(self, query_string):
        """快速提取设备ID"""
        import urllib.parse
        params = urllib.parse.parse_qs(query_string)
        return params.get('device_id', ['unknown'])[0]

    async def disconnect(self, close_code):
        """快速断开处理"""
        print(f"🔌 {self.client_type} 断开: {close_code}")

    async def receive(self, text_data):
        """
        高性能消息处理 - 最小化延迟
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # 快速处理性能配置
            if message_type == 'performance_config':
                await self.send_immediately({
                    'type': 'performance_ack',
                    'status': 'high_performance_mode',
                    'timestamp': time.time()
                })
                return

            # 根据客户端类型快速路由
            if self.client_type == 'hid_reader':
                await self.process_hid_reader_message(data)
            else:
                await self.process_web_client_message(data)

        except Exception as e:
            # 快速错误响应
            await self.send_immediately({
                'type': 'error',
                'message': '消息处理失败',
                'timestamp': time.time()
            })

    async def hid_action(self, event):
        """
        优化版 hid_action - 最小化处理延迟
        """
        action_data = event['action']

        # 立即发送，不等待任何处理
        await self.send_immediately(action_data)

    async def process_hid_reader_message(self, data):
        """
        优化版 HID 读取器消息处理
        """
        message_type = data.get('type')

        if message_type == 'hid_data':
            await self.process_hid_data_optimized(data)
        elif message_type == 'ping':
            await self.send_immediately({'type': 'pong', 'timestamp': time.time()})
        else:
            await self.send_immediately({
                'type': 'error',
                'message': f'未知消息类型: {message_type}',
                'timestamp': time.time()
            })

    async def process_hid_data_optimized(self, data):
        """
        高性能 HID 数据处理 - 直接转发，最小化处理
        """
        try:
            hid_data = data.get('data', {})

            # 快速处理 HID 数据
            display_events = HIDService.process_structured_hid_data(hid_data)

            if not display_events:
                return

            # 立即构建批量更新消息
            batch_event = {
                'type': 'batch_display_update',
                'events': display_events,
                'total_events': len(display_events),
                'timestamp': time.time(),
                'high_priority': True
            }

            # 直接广播，不等待
            asyncio.create_task(self.broadcast_immediately(batch_event))

            # 快速响应给 HID 读取器
            await self.send_immediately({
                'type': 'processing_result',
                'display_events_count': len(display_events),
                'message': '状态更新已发送',
                'timestamp': time.time()
            })

        except Exception as e:
            await self.send_immediately({
                'type': 'error',
                'message': f'数据处理错误: {str(e)}',
                'timestamp': time.time()
            })

    async def broadcast_immediately(self, event_data):
        """
        立即广播，不等待结果
        """
        try:
            await self.channel_layer.group_send(
                "web_clients",
                {
                    'type': 'hid_action',
                    'action': event_data
                }
            )
        except Exception as e:
            print(f"❌ 广播失败: {e}")

    async def send_immediately(self, data):
        """
        立即发送消息，不进行复杂处理
        """
        try:
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            print(f"❌ 发送失败: {e}")

    async def process_web_client_message(self, data):
        """
        处理前端消息 - 简化版本
        """
        message_type = data.get('type')

        if message_type == 'ping':
            await self.send_immediately({
                'type': 'pong',
                'timestamp': time.time()
            })
        elif message_type == 'request_status':
            await self.send_immediately({
                'type': 'system_status',
                'hid_connected': True,
                'timestamp': time.time()
            })