# button_printer/consumers.py
import json
import asyncio
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from .services import HIDService


class HIDConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_type = None  # 'hid_reader' 或 'web_client'
        self.device_id = None

    async def connect(self):
        """WebSocket连接建立"""
        print("=" * 50)
        print("🔗 WebSocket 连接请求收到")

        await self.accept()
        await self.send(json.dumps({
            'type': 'performance_mode',
            'enabled': True,
            'timestamp': time.time()
        }))

        # 可以根据查询参数区分客户端类型
        query_string = self.scope.get('query_string', b'').decode()
        if 'client_type=hid_reader' in query_string:
            self.client_type = 'hid_reader'
            self.device_id = self.get_device_id_from_query(query_string)
            print(f"✅ HID读取器连接: {self.device_id}")
        else:
            self.client_type = 'web_client'
            print(f"✅ 前端客户端连接")

        # 加入广播组（重要！）
        await self.channel_layer.group_add("web_clients", self.channel_name)
        print(f"✅ 客户端已加入广播组: web_clients")
        print(f"✅ 频道名称: {self.channel_name}")

        # 发送连接确认
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'client_type': self.client_type,
            'message': 'WebSocket连接已建立'
        }))
        print("✅ 连接确认消息已发送")
        print("=" * 50)

    def get_device_id_from_query(self, query_string):
        """从查询字符串中提取设备ID"""
        import urllib.parse
        params = urllib.parse.parse_qs(query_string)
        return params.get('device_id', ['unknown'])[0]

    async def disconnect(self, close_code):
        """WebSocket连接断开"""
        if self.client_type == 'hid_reader':
            print(f"❌ HID读取器断开: {self.device_id}, 代码: {close_code}")
        else:
            print(f"❌ 前端客户端断开, 代码: {close_code}")

    async def receive(self, text_data):
        """
        高性能消息处理 - 立即转发不阻塞
        """
        try:
            data = json.loads(text_data)

            # 如果是性能配置请求
            if data.get('type') == 'performance_config':
                await self.send(json.dumps({
                    'type': 'performance_ack',
                    'status': 'high_performance_mode',
                    'timestamp': time.time()
                }))
                return

        except json.JSONDecodeError:
            # 快速失败，不阻塞
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON',
                'timestamp': time.time()
            }))

        except Exception as e:
            await self.send_error(f"消息处理错误: {str(e)}")

    async def hid_action(self, event):
        """处理从 HID 服务发来的显示事件"""
        print("=" * 50)
        print("🎯 开始处理 hid_action 广播消息")
        print("=" * 50)

        action_data = event['action']

        print(f"📤 收到广播消息类型: {action_data.get('type')}")
        print(f"📊 总事件数量: {action_data.get('total_events', 0)}")
        print(f"🎯 目标频道: {self.channel_name}")

        # 分析显示状态事件列表
        if 'events' in action_data and action_data['events']:
            events = action_data['events']
            print(f"📋 显示状态事件列表详情 ({len(events)} 个事件):")

            # 统计显示和隐藏的数量
            visible_count = sum(1 for e in events if e.get('visible'))
            hidden_count = len(events) - visible_count

            print(f"   👁️  显示: {visible_count} 个按钮")
            print(f"   🙈  隐藏: {hidden_count} 个按钮")

            # 显示每个事件的详细信息
            for i, event_item in enumerate(events):
                key = event_item.get('key', '未知')
                visible = event_item.get('visible')
                status = "🟢 显示" if visible else "🔴 隐藏"
                print(f"   {i + 1:2d}. {status} - 按键: {key}")

        else:
            print("⚠️  没有显示状态事件或事件列表为空")

        print(f"🎯 准备发送给前端频道: {self.channel_name}")

        # 发送给前端
        try:
            await self.send(text_data=json.dumps(action_data))
            print("✅ 显示状态事件已成功发送到前端")
        except Exception as e:
            print(f"❌ 发送到前端失败: {e}")

        print("=" * 50)
        print("✅ hid_action 处理完成")
        print("=" * 50)

    async def hid_error(self, event):
        """处理错误消息"""
        error_data = event['error']
        print(f"❌ 发送错误信息到前端: {error_data}")
        await self.send(text_data=json.dumps(error_data))

    async def handle_hid_reader_message(self, data):
        """处理HID读取器的消息"""
        message_type = data.get('type')

        if message_type == 'hid_data':
            await self.process_hid_data(data)
        elif message_type == 'device_status':
            await self.handle_device_status(data)
        elif message_type == 'ping':
            await self.send_pong()
        else:
            await self.send_error(f"未知的HID消息类型: {message_type}")

    async def handle_web_client_message(self, data):
        """处理前端客户端的消息"""
        message_type = data.get('type')

        if message_type == 'ping':
            await self.send_pong()
        elif message_type == 'request_status':
            await self.send_system_status()
        else:
            await self.send_error(f"未知的前端消息类型: {message_type}")

    async def process_hid_data(self, data):
        """处理 HID 数据，传递多个按键的显示状态"""
        try:
            print(f"🎮 收到 HID 数据: {data}")

            hid_data = data.get('data', {})

            # 获取显示状态事件列表
            display_events = HIDService.process_structured_hid_data(hid_data)

            print(f"📦 收到 {len(display_events)} 个显示状态事件")
            for i in display_events:
                print(i)
                print("-----------------------------------------")
            # 批量发送所有显示状态事件
            batch_event = {
                'type': 'batch_display_update',
                'events': display_events,  # 包含所有按键显示状态的列表
                'total_events': len(display_events)
            }

            print(f"📤 批量发送显示状态更新")

            # 通过 Channel Layer 广播给所有前端客户端
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                "web_clients",
                {
                    'type': 'hid_action',
                    'action': batch_event
                }
            )

            # 发送处理结果给 HID 读取器
            await self.send(text_data=json.dumps({
                'type': 'processing_result',
                'display_events_count': len(display_events),
                'message': f'更新了 {len(display_events)} 个按键的显示状态'
            }))

        except Exception as e:
            print(f"❌ HID数据处理错误: {e}")
            import traceback
            traceback.print_exc()

    async def broadcast_to_web_clients(self, events, device_id):
        """将事件广播给所有前端客户端"""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        for event in events:
            action = HIDService.handle_hid_event(event)
            action['device_id'] = device_id
            action['timestamp'] = asyncio.get_event_loop().time()

            # 广播给所有Web客户端组
            await channel_layer.group_send(
                "web_clients",
                {
                    'type': 'hid_action',
                    'action': action
                }
            )

    async def hid_action(self, event):
        """处理群组广播消息"""
        action = event['action']
        await self.send(text_data=json.dumps(action))

    async def handle_device_status(self, data):
        """处理设备状态消息"""
        status = data.get('status')
        device_id = data.get('device_id')
        print(f"📊 设备状态更新: {device_id} -> {status}")

    async def send_pong(self):
        """发送Pong响应"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': asyncio.get_event_loop().time()
        }))

    async def send_system_status(self):
        """发送系统状态"""
        await self.send(text_data=json.dumps({
            'type': 'system_status',
            'hid_connected': True,
            'clients_count': 1,  # 这里可以统计实际连接数
            'timestamp': asyncio.get_event_loop().time()
        }))

    async def send_error(self, error_message):
        """发送错误信息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'client_type': self.client_type
        }))
