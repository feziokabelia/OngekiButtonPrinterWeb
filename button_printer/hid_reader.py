import asyncio
import configparser
import math
import struct
from ctypes import cdll
from datetime import datetime

import websockets
import json
import time
import sys
import os

config = configparser.ConfigParser()


# 获取exe所在目录的路径
def get_exe_dir():
    """获取exe或脚本所在目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


try:
    config_path = os.path.abspath('config.ini')
    # config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    # config_path = os.path.join(get_exe_dir(), 'config.ini')
    # print(config_path)
    config.read(config_path)
    DEVICE_NAME = str(config.get('device', 'device_name'))
    idk = int(config.get('idk', 'idk'))
    fre = float(config.get('frequency', 'fre'))
    # print(idk)
    if DEVICE_NAME == 'io4':
        VENDOR_ID = 0x0CA3
        PRODUCT_ID = 0x0021
    elif DEVICE_NAME == 'ontroller':
        VENDOR_ID = 0x0E8F
        PRODUCT_ID = 0x1002
    elif DEVICE_NAME == 'nageki':
        VENDOR_ID = 0x2341
        PRODUCT_ID = 0x8036
    else:
        raise ValueError('device_name error or device not supported')

except configparser.Error as e:
    print(e)
    print("fail to read config.ini")
except ValueError as e:
    print(e)
    with open('config_error.txt', 'w', encoding='utf-8') as file:
        file.write(f"{e}")
    sys.exit()

# hidapi.dll位置
dll_path = os.path.abspath('hidapi.dll')
# dll_path = os.path.join(get_exe_dir(), 'hidapi.dll')
# 加载hid
try:
    # print(dll_path)
    cdll.LoadLibrary(dll_path)  # 使用绝对路径
    import hid
    # print(f"成功加载 hidapi!  路径{dll_path}")
except Exception as e:
    with open('hid_error.log', 'w') as file:
        file.write("fail to load hidapi.dll!")
        file.write(str(e))
    print(f"加载失败: {e}")
    sys.exit()
OUTPUT_T_FORMAT = '<8h 4h 2B 2B 2H 2B 29x'  # 小端字节序，2B 2B 表示 2个 coin_data_t（每个2字节）
button_positions = [11, 12, 13, 14, 15, 16, 17, 18]  # 左侧→右侧


def parse_output_data(data):
    # 解析前 24 字节（按钮 10B + 摇杆 H + 扫描 B + AimiId 10B + 测试按钮 B）
    fmt = "<10BhB10BB"  # 小端序
    unpacked = struct.unpack(fmt, data[:24])
    buttons = unpacked[:10]
    lever = unpacked[10]
    scan = unpacked[11]
    aimi_id = unpacked[12:22]
    opt_button = unpacked[22]
    return buttons, lever, scan, aimi_id, opt_button


class RealHIDWebSocketReader:
    def __init__(self, vendor_id=VENDOR_ID, product_id=PRODUCT_ID, websocket_url="ws://127.0.0.1:8000/ws/hid/"):
        """
        初始化真实 HID 设备读取器

        参数:
            vendor_id: HID设备厂商ID (十六进制)
            product_id: HID设备产品ID (十六进制)
            websocket_url: WebSocket服务器地址
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.websocket_url = websocket_url

        # 连接状态
        self.is_connected = False
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0

        # HID设备
        self.hid_device = None
        self.polling_interval = fre  # 25ms读取延迟

        # 数据
        self.data = None

        # 设备信息
        self.device_id = f"hid_{vendor_id:04x}_{product_id:04x}"

        print(f"🎮 初始化 HID 设备读取器")
        print(f"  设备: {vendor_id:04x}:{product_id:04x}")
        print(f"  WebSocket: {websocket_url}")

    async def connect_to_websocket(self):
        """连接到WebSocket服务器"""
        try:
            # 添加查询参数标识为HID读取器
            query_params = f"?client_type=hid_reader&device_id={self.device_id}"
            full_url = f"{self.websocket_url}{query_params}"

            print(f"🔗 正在连接到 WebSocket: {full_url}")
            self.websocket = await websockets.connect(full_url, ping_interval=20, ping_timeout=10)
            self.is_connected = True
            self.reconnect_attempts = 0

            # 等待连接确认消息
            response = await self.websocket.recv()
            response_data = json.loads(response)
            print(f"✅ WebSocket 连接成功: {response_data.get('message')}")

            return True

        except Exception as e:
            print(f"❌ WebSocket 连接失败: {e}")
            return False

    def initialize_hid_device(self):
        """初始化真实HID设备"""
        try:
            print(f"🎮 正在打开 HID 设备: {self.vendor_id:04x}:{self.product_id:04x}")

            # 查找并打开设备
            # self.hid_device = hid.Device(self.vendor_id, self.product_id)
            self.hid_device = hid.device()
            self.hid_device.open(self.vendor_id, self.product_id)
            print(f"✅ HID设备打开成功:")
            return True

        except Exception as e:
            print(f"❌ HID设备初始化未知错误: {e}")
            print(f"❌ 检查config.ini中device_name是否为你的设备")
            with open('hid_reader_error.log', 'a') as file:
                file.write(f"---{str(datetime.now())}\n")
                file.write(f"HID设备初始化错误: {e}\n")
                file.write("检查config.ini中device_name是否为你的设备\n")
                file.write("---\n")
            print(f"加载失败: {e}")
            return False

    def read_hid_data(self):
        """读取真实HID设备数据"""
        try:
            if not self.hid_device:
                return None

            # 读取数据（非阻塞）
            # 大多数HID设备报告长度为64字节
            if DEVICE_NAME == 'io4':
                data = self.hid_device.read(63)
            elif DEVICE_NAME == 'ontroller':

                if idk == 1:
                    data = self.hid_device.read(5)
                else:
                    data = self.hid_device.read(64)

            elif DEVICE_NAME == 'nageki':
                data = self.hid_device.read(64)  # 记得改

            if self.data != data:
                self.data = data
                if data:
                    # 打印原始数据用于调试
                    hex_data = ' '.join(f'{b:02x}' for b in data)
                    print(f"📥 原始HID数据: [{hex_data}]")

                    # 解析数据
                    unpacked_data = self.parse_hid_data(bytes(data))
                    return unpacked_data
                else:
                    # 没有数据可用是正常的（非阻塞模式）
                    return None

        except Exception as e:
            print(f"❌ HID读取错误: {e}")
            # 如果读取失败，尝试重新初始化设备
            self.reinitialize_hid_device()
            return None

    def parse_hid_data(self, data):
        """解析输出数据，仅提取指定字段"""
        if DEVICE_NAME == 'io4':
            unpacked = struct.unpack(OUTPUT_T_FORMAT, data)
            return {
                'rotary': tuple(unpacked[8:12]),  # 后续4个int16_t (旋转编码器)
                'switches': tuple(unpacked[16:18]),  # 2个uint16_t (开关状态)
                'system_status': unpacked[18]  # uint8_t (系统状态)
            }

        elif DEVICE_NAME == 'ontroller':
            if idk == 0:
                op = {
                    "sub_pos": data[2],  # int
                    "pos": data[1],  # int
                    "key": f"{data[3]:08b}",  # str
                }
                return op
            else:
                binary_chars = []
                for pos in button_positions:
                    if data[pos] == 0x01:  # 按键按下
                        binary_chars.append('1')
                    else:  # 按键释放
                        binary_chars.append('0')

                op = {
                    "sub_pos": data[22],  # int
                    "pos": data[21],  # int
                    "key": ''.join(binary_chars),  # str
                }
                return op

        elif DEVICE_NAME == 'nageki':
            b_data = bytes(data)
            buttons, lever, scan, aimi_id, opt_button = parse_output_data(b_data)
            button_s = ""
            for i in range(len(buttons)):
                button_s = button_s + str(buttons[i])
            op = {
                "sub_pos": lever,  # int
                "pos": lever,  # int
                "key": button_s,  # str
            }
            return op

    def reinitialize_hid_device(self):
        """重新初始化HID设备"""
        print("🔄 尝试重新初始化HID设备...")
        self.cleanup_hid_device()
        time.sleep(1)
        return self.initialize_hid_device()

    def cleanup_hid_device(self):
        """清理HID设备"""
        if self.hid_device:
            try:
                self.hid_device.close()
                self.hid_device = None
                print("✅ HID设备已关闭")
            except:
                pass

    async def send_hid_data(self, unpacked_data):
        """发送HID数据到WebSocket服务器"""
        try:
            if not self.is_connected or not self.websocket:
                print("⚠️ WebSocket未连接，无法发送数据")
                return False

            # 确保数据可以被 JSON 序列化
            if DEVICE_NAME == "io4":
                serializable_data = {
                    'type': 'hid_data',
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'data': {
                        'rotary': list(unpacked_data.get('rotary', (0, 0, 0, 0))),  # 转换为列表
                        'switches': list(unpacked_data.get('switches', (0, 0))),  # 转换为列表
                        'system_status': int(unpacked_data.get('system_status', 0)),  # 确保是整数
                        'DEVICE_NAME': DEVICE_NAME
                    }
                }
            else:
                serializable_data = {
                    'type': 'hid_data',
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'data': {
                        "sub_pos": unpacked_data.get('sub_pos'),  # int
                        "pos": unpacked_data.get('pos'),  # int
                        "key": unpacked_data.get('key'),  # str
                        'DEVICE_NAME': DEVICE_NAME,
                        'idk': idk
                    }
                }

            await self.websocket.send(json.dumps(serializable_data))
            print(f"📤 发送HID数据: {unpacked_data}")
            return True

        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket连接已关闭")
            self.is_connected = False
            return False
        except Exception as e:
            print(f"❌ 发送HID数据失败: {e}")
            self.is_connected = False
            return False

    async def receive_messages(self):
        """接收WebSocket服务器消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_server_message(data)

        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket连接已关闭")
            self.is_connected = False
        except Exception as e:
            print(f"❌ 接收消息错误: {e}")
            self.is_connected = False

    async def handle_server_message(self, message):
        """处理服务器返回的消息"""
        message_type = message.get('type')
        print("✅    处理服务器返回的消息")
        if message_type == 'processing_result':
            button_key = message.get('display_events_count', 'unknown')
            print(f"图片处理列表长度     {button_key}")

    async def send_ping(self):
        """发送心跳包"""
        try:
            if self.is_connected:
                await self.websocket.send(json.dumps({"type": "ping"}))
        except:
            self.is_connected = False

    async def run(self):
        """主运行循环"""
        print("🚀 启动真实 HID 设备读取器...")

        # 初始化HID设备
        if not self.initialize_hid_device():
            print("❌ HID设备初始化失败，退出")
            return

        # 连接WebSocket
        while self.reconnect_attempts < self.max_reconnect_attempts:
            if await self.connect_to_websocket():
                break

            self.reconnect_attempts += 1
            print(f"🔄 {self.reconnect_attempts}/{self.max_reconnect_attempts} 尝试重新连接...")
            await asyncio.sleep(self.reconnect_delay)
        else:
            print("❌ 达到最大重连次数，退出")
            return

        try:
            # 启动消息接收任务
            receive_task = asyncio.create_task(self.receive_messages())

            # 主数据读取循环
            last_ping_time = time.time()
            data_count = 0

            print("🎯 开始HID数据读取循环...")

            while self.is_connected:
                # 读取HID数据
                hid_data = self.read_hid_data()

                if hid_data:
                    # 发送HID数据
                    success = await self.send_hid_data(hid_data)
                    if success:
                        data_count += 1
                        if data_count % 50 == 0:  # 每50条数据打印一次统计
                            print(f"📊 已发送 {data_count} 条HID数据")

                # 定期发送心跳
                current_time = time.time()
                if current_time - last_ping_time > 30:  # 30秒一次心跳
                    await self.send_ping()
                    last_ping_time = current_time

                # 控制读取频率
                await asyncio.sleep(self.polling_interval)

            # 等待接收任务完成
            await receive_task

        except KeyboardInterrupt:
            print("\n🛑 用户中断")
        except Exception as e:
            print(f"❌ 运行错误: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        print("🧹 清理资源...")
        self.is_connected = False

        if hasattr(self, 'websocket'):
            await self.websocket.close()

        self.cleanup_hid_device()
        print("✅ 资源清理完成")


def list_hid_devices():
    """列出所有可用的HID设备"""
    try:
        import hid
        print("🔍 扫描可用的HID设备...")

        for device_info in hid.enumerate():
            vendor_id = device_info['vendor_id']
            product_id = device_info['product_id']
            manufacturer = device_info['manufacturer_string']
            product = device_info['product_string']
            usage_page = device_info['usage_page']
            usage = device_info['usage']

            print(f"  {vendor_id:04x}:{product_id:04x} - {manufacturer} - {product}")
            print(f"    Usage Page: {usage_page}, Usage: {usage}")
            print(f"    Path: {device_info['path']}")
            print()

    except ImportError:
        print("❌ 未找到hidapi库，无法扫描设备")
    except Exception as e:
        print(f"❌ 扫描设备失败: {e}")


async def main():
    """主函数"""

    # 创建读取器实例
    reader = RealHIDWebSocketReader(
        vendor_id=VENDOR_ID,
        product_id=PRODUCT_ID,
        websocket_url="ws://127.0.0.1:8000/ws/hid/"
    )

    await reader.run()


if __name__ == "__main__":
    # 运行HID读取器
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序退出")
