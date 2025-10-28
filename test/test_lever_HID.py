# 获取exe所在目录的路径
import configparser
import os
import struct
import sys
import time
from ctypes import cdll
from datetime import datetime
from enum import IntEnum

config = configparser.ConfigParser()
temp_max = 0
temp_min = 999


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


class CoinCondition(IntEnum):
    NORMAL = 0x0
    JAM = 0x1
    DISCONNECT = 0x2
    BUSY = 0x3


# 定义 output_t 的解析格式（小端字节序）
OUTPUT_T_FORMAT = '<8h 4h 2B 2B 2H 2B 29x'  # 小端字节序，2B 2B 表示 2个 coin_data_t（每个2字节）
STRUCT_SIZE = struct.calcsize(OUTPUT_T_FORMAT)
# print(f"Struct size: {STRUCT_SIZE} bytes")  # 应输出 63
output_count = 0

last_Analog = [0, 0]


def read_hid_device():
    global output_count
    last_data = None  # 缓存上一次的数据
    # device = hid.Device(VENDOR_ID, PRODUCT_ID)
    device = hid.device()
    device.open(VENDOR_ID, PRODUCT_ID)
    while True:
        data = device.read(STRUCT_SIZE)
        if not data:
            continue
        current_data = parse_output_t(bytes(data))
        # print(current_data['rotary'])

        # 仅当数据变化时输出
        if data_changed(last_data, current_data):
            print(f"{current_data['rotary'][1]}")
            last_data = current_data  # 更新缓存


def data_changed(old, new):
    if old is None:
        return True  # 第一次总是输出
    return (
            old['analog'] != new['analog'] or
            old['rotary'] != new['rotary'] or
            old['coin'] != new['coin'] or
            old['switches'] != new['switches'] or
            old['system_status'] != new['system_status'] or
            old['usb_status'] != new['usb_status']
    )


def parse_output_t(data: bytes):
    unpacked = struct.unpack(OUTPUT_T_FORMAT, data)
    return {
        'analog': unpacked[:8],
        'rotary': unpacked[8:12],
        'coin': [
            {'condition': CoinCondition(unpacked[12]), 'count': unpacked[13]},
            {'condition': CoinCondition(unpacked[14]), 'count': unpacked[15]}
        ],
        'switches': unpacked[16:18],
        'system_status': unpacked[18],
        'usb_status': unpacked[19],
    }


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


def detect_packet_size():
    global temp_max, temp_min, device
    last_data = None
    # device = hid.Device(vendor_id, product_id)
    try:
        # device = hid.Device(VENDOR_ID, PRODUCT_ID)
        device = hid.device()
        device.open(VENDOR_ID, PRODUCT_ID)
    except Exception as e:
        with open("error.txt", "a") as f:
            f.write(f"error: {e} -- {datetime.datetime.now()} \n")
    print("开始读取")
    try:
        while True:
            print("进入循环")
            data = device.read(5)
            print("完整数据")
            if not data:
                time.sleep(0.1)
                continue
            j = 0
            for byte in data:
                print(f"{j}    {byte}")
                j = j + 1

            i = 0
            if last_data != data:
                for byte in data:
                    if i == 1:  # data[1]
                        if temp_max < byte:
                            temp_max = byte
                        if temp_min > byte:
                            temp_min = byte
                        print(byte)
                    i = i + 1
                print("------------------------------")
                last_data = data
    except KeyboardInterrupt:
        print(" ")


def monitor_hid_device():
    # 打开设备
    last_data = None
    try:
        device = hid.device()
        device.open(VENDOR_ID, PRODUCT_ID)
        print(f"设备已连接: {device.get_product_string()}")
    except Exception as e:
        device = hid.Device(VENDOR_ID, PRODUCT_ID)

    try:
        while True:
            data = device.read(64)
            if last_data != data:
                if data and len(data) >= 24:
                    b_data = bytes(data)
                    buttons, lever, scan, aimi_id, opt_button = parse_output_data(b_data)

                    print(f"""
                    摇杆: {lever}
                    """)
            last_data = data

    except KeyboardInterrupt:
        print("停止监控")
    finally:
        device.close()


def idk_detect_packet_size():
    global temp_max, temp_min, device
    try:
        device = hid.device()
        device.open(int(VENDOR_ID, 0), int(PRODUCT_ID, 0))

    except Exception as e:
        with open("error.txt", "a") as f:
            f.write(f"error: {e} -- {datetime.datetime.now()} \n")
    print("开始读取")
    try:
        print("进入循环")
        last_data = None
        while True:
            data = device.read(64)
            j = 0
            for t in data:
                if j == 21:
                    if last_data != t:
                        if temp_max < t:
                            temp_max = t
                        if temp_min > t:
                            temp_min = t
                        print(f"摇杆数值：  {t}")
                j = j + 1
                last_data = t
            # print(data)
    except KeyboardInterrupt:
        with open('leverlimit.txt', 'w') as f:
            f.writelines(f"MAX: {temp_max} \n")
            f.writelines(f"MIN: {temp_min} \n")


def io4_lever_detect():
    read_hid_device()


def ontroller_lever_detect():
    detect_packet_size()


def idk_ontroller_lever_detect():
    idk_detect_packet_size()


def nageki_lever_detect():
    monitor_hid_device()


if __name__ == "__main__":
    if DEVICE_NAME == "io4":
        io4_lever_detect()

    elif DEVICE_NAME == "ontroller":
        if idk == 0:
            ontroller_lever_detect()
        else:
            idk_ontroller_lever_detect()

    elif DEVICE_NAME == "nageki":
        nageki_lever_detect()

