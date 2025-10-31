# button_printer/services.py
import configparser
import math
import os
import sys
import keyboard

OUTPUT_T_FORMAT = '<8h 4h 2B 2B 2H 2B 29x'  # 小端字节序，2B 2B 表示 2个 coin_data_t（每个2字节）

LW = "31"
LR = "0"
LG = "5"
LB = "4"

RR = "1"
RG = "16"
RB = "15"
RW = "14"

key_map_io4 = {
    # 索引0
    0: {
        7: LR,  # 左1（第7位）
        2: LG,  # 左2（第2位）
        3: LB,  # 左3（第3位）
        6: RR,  # 右1（第6位）
    },
    # 索引1
    1: {
        7: RG,  # 右2（第7位）
        8: RB,  # 右3（第8位）
        9: RW  # 右侧
    }
}
key_map_o = {
    7: LR,
    6: LG,
    5: LB,
    4: RR,
    3: RG,
    2: RB,
    1: LW,
    0: RW
}
key_map_o_idk = {
    0: LR,
    1: LG,
    2: LB,
    3: RR,
    4: RG,
    5: RB,
    7: LW,
    6: RW
}
key_map_na = {
    0: LR,
    1: LG,
    2: LB,
    5: RR,
    6: RG,
    7: RB,
    3: LW,
    8: RW

}

# 键盘对应HID表
HID2KM = {
    '31': "s",
    '0': "d",
    '5': "f",
    '4': "g",
    '1': "h",
    '16': "j",
    '15': "k",
    '14': "l",
}
key_states = {key: False for key in [LW, LR, LG, LB, RR, RG, RB, RW]}

config = configparser.ConfigParser()


def get_config_path():
    """获取config.ini文件的路径"""
    if getattr(sys, 'frozen', False):
        # 打包模式 - 从EXE所在目录读取
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发模式 - 从脚本所在目录读取
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 在EXE所在目录查找config.ini
    config_path = os.path.join(base_dir, 'config.ini')
    return config_path


try:
    # config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config_path = get_config_path()
    print(f"config_path                {config_path}")
    config.read(config_path)
    L_MAX = int(config.get('boundary', 'L_MAX'))
    R_MAX = int(config.get('boundary', 'R_MAX'))
    # 摇杆边界值设定 [L_MAX L2] [L2 L1] [L1 R1] [R1 R2] [R2 R_MAX]
    if L_MAX < R_MAX:
        temp = L_MAX
        L_MAX = R_MAX
        R_MAX = temp
    space = math.ceil((L_MAX - R_MAX) / 5)
    L_2 = L_MAX - space
    L_1 = L_2 - space
    R_1 = L_1 - space
    R_2 = R_1 - space
except configparser.Error as e:
    print(e)
    print("fail to read config.ini")


def close_swing(events):
    lever_str = {"lever_0", "lever_1", "lever_-1", "lever_2", "lever_-2"}
    for i in lever_str:
        events.append({'key': i, 'visible': False, })
    return events


def show_lever_KM(x, events):
    result = []
    # 显示摇杆
    position = x  # 摇杆位置
    pos_image = HIDService.get_pos(position)  # 摇杆位置的图片
    sub_pos = HIDService.get_sub_position(x)
    # print("---------------------------------------------")
    # print(position)
    is_l_buttons = False
    is_r_buttons = False
    release_button_i = 0
    # print(LW)
    for i in (LW, LR, LG, LB, RR, RG, RB, RW):
        if release_button_i < 4:  # 左侧
            if HIDService.release_button[i] == 1:
                is_l_buttons = True
        else:
            if HIDService.release_button[i] == 1:
                # print("右侧有键")
                is_r_buttons = True
        release_button_i = release_button_i + 1
    last_lever_pos = HIDService.last_lever_pos
    if HIDService.last_lever_pos != position:  # 左侧有按键则不显示摇杆 右侧同
        events = close_swing(events)
        if HIDService.last_lever_pos != "":
            events.append({'key': "l_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
            events.append({'key': "r_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
        # print(f"{is_l_buttons}  {is_r_buttons}")
        if HIDService.last_button != "":
            events.append({'key': HIDService.last_button, 'visible': False, })
        if is_l_buttons and is_r_buttons:  # 情况1 左右两侧都有按键
            # print("情况1")
            events.append({'key': "l_" + pos_image, 'visible': False, })
            events.append({'key': "r_" + pos_image, 'visible': False, })
            events.append({'key': pos_image, 'visible': True, })
        else:
            events.append({'key': "bg_swing", 'visible': False, })
        if is_l_buttons and not is_r_buttons:  # 情况2 左侧有 右侧没有
            # print("情况2")
            # print("l_" + pos_image)
            HIDService.is_show_bg_l0 = True
            HIDService.is_left = False
            events.append({'key': pos_image, 'visible': False, })
            events.append({'key': "l_" + pos_image, 'visible': True, })
            events.append({'key': "r_" + pos_image, 'visible': False, })
        else:
            HIDService.is_show_bg_l0 = False
        if not is_l_buttons and is_r_buttons:  # 情况3 右侧有 左侧没有
            # print("情况3")
            HIDService.is_show_bg_r0 = True
            HIDService.is_left = True
            events.append({'key': pos_image, 'visible': False, })
            events.append({'key': "l_" + pos_image, 'visible': False, })
            events.append({'key': "r_" + pos_image, 'visible': True, })

        else:
            HIDService.is_show_bg_r0 = False
        if not is_l_buttons and not is_r_buttons:  # 情况4 都没有
            # print("情况4")
            # print(self.is_left)
            if HIDService.is_left:
                # print("换右")
                HIDService.is_show_bg_r0 = True
                events.append({'key': pos_image, 'visible': False, })
                events.append({'key': "r_" + pos_image, 'visible': True, })  # 换默认右
            else:
                # print("换左")
                HIDService.is_show_bg_l0 = True
                events.append({'key': pos_image, 'visible': False, })
                events.append({'key': "l_" + pos_image, 'visible': True, })  # 换默认左
        HIDService.last_lever_pos = position
    elif HIDService.last_lever_pos == position:  # 摇杆不动 手放下
        if HIDService.last_subpos == sub_pos:
            # self.bg_item_swing.setVisible(True)
            events.append({'key': pos_image, 'visible': True, })
            HIDService.is_show_bg_r0 = True
            HIDService.is_show_bg_l0 = True
            events.append({'key': "l_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
            events.append({'key': "r_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
        HIDService.last_subpos = sub_pos
    result.append(last_lever_pos)
    result.append(events)
    return result


def show_lever(data_hid, key_data, pressed_keys, events, device_name):
    result = []
    # 显示摇杆
    if device_name == "io4":
        position = data_hid.get('rotary')[1]
        pos_image = HIDService.get_pos(position)
        sub_pos = HIDService.get_sub_position(data_hid.get('rotary')[0])
        key_map = key_map_io4
        # print(sub_pos)
    else:
        # 显示摇杆
        if device_name == "nageki":
            key_map = key_map_na
        if device_name == "ontroller":
            if int(data_hid.get("idk")) == 0:
                key_map = key_map_o
            else:
                key_map = key_map_o_idk
        position = data_hid.get("pos")  # 摇杆位置
        pos_image = HIDService.get_pos(position)
        sub_pos = HIDService.get_sub_position(data_hid.get("sub_pos"))
        # print(sub_pos)

    is_l_buttons = False
    is_r_buttons = False
    release_button_i = 0
    for i in (LW, LR, LG, LB, RR, RG, RB, RW):
        if release_button_i < 4:  # 左侧
            if HIDService.release_button[i] == 1:
                is_l_buttons = True
        else:
            if HIDService.release_button[i] == 1:
                # print("右侧有键")
                is_r_buttons = True
        release_button_i = release_button_i + 1
    last_lever_pos = HIDService.last_lever_pos
    if HIDService.last_lever_pos != position:  # 左侧有按键则不显示摇杆 右侧同
        events = close_swing(events)
        if HIDService.last_lever_pos != "":
            events.append({'key': "l_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
            events.append({'key': "r_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
        # print(f"{is_l_buttons}  {is_r_buttons}")
        if HIDService.last_button != "":
            events.append({'key': HIDService.last_button, 'visible': False, })
        if is_l_buttons and is_r_buttons:  # 情况1 左右两侧都有按键
            # print("情况1")
            events.append({'key': "l_" + pos_image, 'visible': False, })
            events.append({'key': "r_" + pos_image, 'visible': False, })
            events.append({'key': pos_image, 'visible': True, })
        else:
            events.append({'key': "bg_swing", 'visible': False, })
        if is_l_buttons and not is_r_buttons:  # 情况2 左侧有 右侧没有
            # print("情况2")
            # print("l_" + pos_image)
            HIDService.is_show_bg_l0 = True
            HIDService.is_left = False
            events.append({'key': pos_image, 'visible': False, })
            events.append({'key': "l_" + pos_image, 'visible': True, })
            events.append({'key': "r_" + pos_image, 'visible': False, })
        else:
            HIDService.is_show_bg_l0 = False
        if not is_l_buttons and is_r_buttons:  # 情况3 右侧有 左侧没有
            # print("情况3")
            HIDService.is_show_bg_r0 = True
            HIDService.is_left = True
            events.append({'key': pos_image, 'visible': False, })
            events.append({'key': "l_" + pos_image, 'visible': False, })
            events.append({'key': "r_" + pos_image, 'visible': True, })

        else:
            HIDService.is_show_bg_r0 = False
        if not is_l_buttons and not is_r_buttons:  # 情况4 都没有
            # print("情况4")
            # print(self.is_left)
            if HIDService.is_left:
                # print("换右")
                HIDService.is_show_bg_r0 = True
                events.append({'key': pos_image, 'visible': False, })
                events.append({'key': "r_" + pos_image, 'visible': True, })  # 换默认右
            else:
                # print("换左")
                HIDService.is_show_bg_l0 = True
                events.append({'key': pos_image, 'visible': False, })
                events.append({'key': "l_" + pos_image, 'visible': True, })  # 换默认左
        HIDService.last_lever_pos = position
    elif HIDService.last_lever_pos == position:  # 摇杆不动 手放下
        if HIDService.last_subpos == sub_pos:
            # self.bg_item_swing.setVisible(True)
            events.append({'key': pos_image, 'visible': True, })
            HIDService.is_show_bg_r0 = True
            HIDService.is_show_bg_l0 = True
            events.append({'key': "l_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
            events.append({'key': "r_" + str(HIDService.get_pos(HIDService.last_lever_pos)), 'visible': False, })
        HIDService.last_subpos = sub_pos
    # print("l_" + pos_image)
    if device_name == "io4":
        for switch_idx in range(2):  # 遍历左/右开关
            for bit_pos in range(16):  # 检查每一位
                new_state = int(key_data[switch_idx][bit_pos])  # 注意：bits[0]是MSB（Bit15）
                if switch_idx == 1 and bit_pos == 9:  # 特殊处理RW
                    if new_state == 0:
                        new_state = 1
                    else:
                        new_state = 0
                if new_state == 1:
                    if switch_idx == 0:
                        key_map_l = key_map.get(switch_idx)
                        for i in key_map_l.keys():
                            if bit_pos == i:
                                pressed_keys.append(key_map_l.get(i))
                    else:
                        key_map_r = key_map.get(switch_idx)
                        for i in key_map_r.keys():
                            if bit_pos == i:
                                pressed_keys.append(key_map_r.get(i))
        if data_hid.get('system_status', 0) == 0:
            pressed_keys.append(LW)
    else:
        for bit_pos in range(len(key_data)):  # 检查每一位
            new_state = int(key_data[bit_pos])
            if new_state == 1:
                for i in key_map.keys():
                    if bit_pos == i:
                        print(i)
                        pressed_keys.append(key_map.get(i))
    result.append(pressed_keys)
    result.append(last_lever_pos)
    result.append(events)
    return result


def m_press(pressed_key, pressed_key_motion, diff1, diff2, last_lever_pos, ):
    HIDService.release_button[pressed_key] = 1
    events = []
    if pressed_key in (LW, LR, LG, LB):
        if last_lever_pos != HIDService.last_lever_pos:
            events.append(HIDService.crete_event("r_" + str(HIDService.get_pos(HIDService.last_lever_pos)), False))
        events.append(HIDService.crete_event("l_0", False))

    else:
        if last_lever_pos != HIDService.last_lever_pos:
            events.append(HIDService.crete_event("l_" + str(HIDService.get_pos(HIDService.last_lever_pos)), False))
        events.append(HIDService.crete_event("r_0", False))

    if pressed_key in (LW, LR, LG, LB, RR, RG, RB, RW):
        # print(f"press = {pressed_key}")
        # print(f"release = {released_key}")
        events.append(HIDService.crete_event(pressed_key, True))
        events.append(HIDService.crete_event(pressed_key_motion, True))
        # print(f"{pressed_key} 显示")

        # 动作图片隐藏的逻辑判断
        if pressed_key in (LW, LR, LG, LB):
            HIDService.left_show = pressed_key_motion
            for le in reversed(range(len(HIDService.last_left_button_arr))):
                if HIDService.last_left_button_arr[le] != "":
                    events.append(HIDService.crete_event(HIDService.last_left_button_arr[le] + "m", False))
        else:
            HIDService.right_show = pressed_key_motion
            for r in reversed(range(len(HIDService.last_right_button_arr))):
                if HIDService.last_right_button_arr[r] != "":
                    events.append(HIDService.crete_event(HIDService.last_right_button_arr[r] + "m", False))
        if not HIDService.last_button == "":
            if HIDService.last_button != pressed_key_motion:
                # 同在左 或 同在右
                if diff1 or diff2:  # 不同边
                    events.append(HIDService.crete_event(HIDService.last_button, False))
        # self.last_button = pressed_key_motion

        if pressed_key_motion in HIDService.left_button:
            # arr = self.last_left_button_arr
            # self.last_left_button_arr[self.last_left_button_i] = pressed_key
            for k in range(len(HIDService.last_left_button_arr)):
                if HIDService.last_left_button_arr[k] == "":
                    HIDService.last_left_button_arr[k] = pressed_key
                    break
            # self.last_left_button_i = self.last_left_button_i + 1
        else:
            # arr = self.last_right_button_arr
            for k in range(len(HIDService.last_right_button_arr)):
                if HIDService.last_right_button_arr[k] == "":
                    HIDService.last_right_button_arr[k] = pressed_key
                    break
    return events


def m_release(pressed_key, pressed_key_motion):
    events = []
    null_count = 0  # 记录last_button_arr有多少“”
    if pressed_key in (LW, LR, LG, LB, RR, RG, RB, RW):
        if HIDService.release_button[pressed_key] == 1:
            # print(f"{pressed_key} 释放")
            left = pressed_key_motion in HIDService.left_button

            if left:
                button_arr = HIDService.last_left_button_arr
                show = HIDService.left_show  # 上一个显示的动作图片
            else:
                button_arr = HIDService.last_right_button_arr
                show = HIDService.right_show  # 同上

            # if left:
            # self.last_left_button_i = self.last_left_button_i - 1
            # else:
            # self.last_right_button_i = self.last_right_button_i - 1

            k = 0  # 当last_button_arr内只有一个按键，记录其下标
            for a in range(len(button_arr)):
                # print(f"数组{i}  {button_arr[i]}")
                if pressed_key == button_arr[a]:
                    # print(f"释放 {button_arr[i]}")
                    if a > 0:
                        # print(f"i {i}")
                        # print(f"该 {button_arr[a-1]} 显示")
                        # print(f"松开前显示的是{show}")

                        # 动作图片显示逻辑判断
                        if button_arr[a - 1] != "":
                            if show != (button_arr[a - 1] + "m") and show != "":
                                # print(f"{button_arr[a - 1]} 显示")
                                events.append(HIDService.crete_event(show, False))
                                events.append(HIDService.crete_event(button_arr[a - 1] + "m", True))
                                if left:
                                    HIDService.left_show = button_arr[a - 1] + "m"
                                else:
                                    HIDService.right_show = button_arr[a - 1] + "m"
                                if button_arr[a] != "":
                                    events.append(HIDService.crete_event(button_arr[a] + "m", False))
                                    button_arr[a] = ""
                                break
                    else:
                        for b in reversed(range(len(button_arr))):
                            if button_arr[b] != "":
                                events.append(HIDService.crete_event(button_arr[b] + "m", True))
                                break
                    button_arr[a] = ""

                else:
                    HIDService.release_button[pressed_key] = 0
                    events.append(HIDService.crete_event(pressed_key, False))
                    events.append(HIDService.crete_event(pressed_key_motion, False))
            for h in range(len(button_arr)):
                if button_arr[h] == "":
                    # print(f"空的位置 {h}")
                    null_count = null_count + 1
                else:
                    # print(f"k = {k}")
                    k = h
            if null_count == 3:
                # print(k)
                # print(f"数组唯一的值 {button_arr[k]}")
                events.append(HIDService.crete_event(button_arr[k] + "m", True))
    return events


class HIDService:
    release_button = {
        LW: 0,
        LR: 0,
        LG: 0,
        LB: 0,
        RR: 0,
        RG: 0,
        RB: 0,
        RW: 0,
    }  # 对应每个按键的按下释放情况  1 按下 0 没按
    right_button = (RR + "m", RG + "m", RB + "m", RW + "m")
    left_button = (LW + "m", LR + "m", LG + "m", LB + "m")
    last_lever_pos = ''
    last_button = ''
    l_motion = ''
    r_motion = ''
    is_show_bg_l0 = False
    is_show_bg_r0 = False
    is_left = True
    first_down = True
    last_subpos = 0
    last_data = ['', ['']]
    left_show = ""
    right_show = ""
    last_left_button_arr = ["", "", "", ""]  # 记录左侧按下情况的数组
    last_left_button_i = 0
    last_right_button_arr = ["", "", "", ""]  # 记录右侧按下情况的数组
    last_right_button_i = 0

    @staticmethod
    def switches_to_binary_strings(switches_data):
        """
        将 switches 数据转换为二进制字符串格式
        switches_data: (0, 64) -> ["0b00000000 00000000", "0b00000000 01000000"]
        """
        try:
            binary_strings = []

            for i, switch_value in enumerate(switches_data):
                # 转换为8位二进制字符串
                binary_str = f"0b{switch_value:08b}"
                # 格式化为可读形式：分成两个4位组
                formatted_str = f"0b{switch_value:08b}"
                binary_strings.append(formatted_str)

                # print(f"🔢 开关字节 {i}: {switch_value} -> {formatted_str}")

            return binary_strings

        except Exception as e:
            print(f"❌ 二进制转换错误: {e}")
            return ["0b00000000 00000000", "0b00000000 00000000"]

    @staticmethod
    def process_structured_hid_data(hid_data):
        """
        直接处理结构化 HID 数据
        避免不必要的格式转换
        """

        #  变量
        global LW, LR, LG, LB, RR, RG, RB, RW
        key = ''
        visible = False
        events = []
        event = {
            'key': key,
            'visible': visible,
        }
        # 显示左右手背景用
        l_flag = 0
        r_flag = 0
        j = 0
        key_data = []
        try:
            # print("-------------------------services--------------------------")
            # print(f"🔧 直接处理结构化 HID 数据: {hid_data}")
            if hid_data.get('DEVICE_NAME') == "io4":
                switches_data = hid_data.get('switches', (0, 0))
                rotary_data = hid_data.get('rotary', (0, 0, 0, 0))
                system_status = hid_data.get('system_status', 0)
                switches_str = [f"0b{s:016b}" for s in switches_data]
                # binary_switches = HIDService.switches_to_binary_strings(switches_str)
                # print(f"🎮 设备状态 - 开关: {switches_str}, 旋钮: {rotary_data}, 系统: {system_status}")
                # 直接分析 switches 数据的二进制位
                for switch in switches_str:
                    bits = switch[2:]  # 去掉 '0b' 前缀
                    # print(bits)
                    # 直接将bits字符串转为列表，并确保长度为16
                    key_data.append(list(bits[:16].ljust(16, '0')))

            elif hid_data.get('DEVICE_NAME') in ('ontroller', 'nageki'):
                key_data = hid_data.get("key")

            elif hid_data.get('DEVICE_NAME') == 'yuangeki':

                # 安装全局钩子
                keyboard.hook(lambda e: None)
                last_lever_pos = show_lever_KM(hid_data.get('x'), events)
                for key_HID in key_states:
                    key = HID2KM.get(key_HID)  # key 键盘
                    current_state = keyboard.is_pressed(key)
                    if current_state != key_states[key_HID]:
                        # print(f"key {key} current_state {current_state}")
                        if current_state:
                            pressed_key_motion = key_HID + "m"

                            # print(f"按下 {key} 键，动作: {pressed_key_motion}")
                            diff1 = (
                                    HIDService.last_button in HIDService.left_button and pressed_key_motion in HIDService.left_button)
                            diff2 = (
                                    HIDService.last_button in HIDService.right_button and pressed_key_motion in HIDService.right_button)
                            if HIDService.release_button[key_HID] == 1:
                                return
                            press = m_press(key_HID, pressed_key_motion, diff1, diff2, last_lever_pos)
                            if press:
                                events = events + press
                        else:
                            # print(f"释放 {key} 键")
                            release = m_release(key_HID, key_HID + "m")
                            if release:
                                events = events + release
                        key_states[key_HID] = current_state

            if hid_data.get("DEVICE_NAME") != 'yuangeki':
                DEVICE_NAME = hid_data.get("DEVICE_NAME")
                pressed_keys = []
                events = []
                # 显示摇杆
                result = show_lever(hid_data, key_data, pressed_keys, events, DEVICE_NAME)
                pressed_keys = result[0]
                last_lever_pos = result[1]
                events = result[2]

                for i in (LW, LR, LG, LB, RR, RG, RW, RB):
                    current = False
                    for ind in range(len(pressed_keys)):
                        if pressed_keys[ind] == i:
                            # print(data_hid)
                            current = True
                    pressed_key = str(i)
                    pressed_key_motion = pressed_key + "m"  # 手部图片

                    # 判断是否同侧
                    diff1 = (
                            HIDService.last_button in HIDService.left_button and pressed_key_motion
                            in HIDService.left_button)
                    diff2 = (
                            HIDService.last_button in HIDService.right_button and pressed_key_motion
                            in HIDService.right_button)

                    if not (pressed_key in (LW, LR, LG, LB, RR, RG, RB, RW)):  # 不在这8个键不会反应
                        continue
                    if current:  # press
                        if HIDService.release_button[pressed_key] == 1:
                            continue
                        press = m_press(pressed_key, pressed_key_motion, diff1, diff2, last_lever_pos)
                        if press:
                            events = events + press
                    else:  # release
                        release = m_release(pressed_key, pressed_key_motion, )
                        if release:
                            events = events + release

            # 判断左边右边分别有多少按键
            for i in HIDService.release_button.keys():
                if j < 4:
                    l_flag = l_flag + HIDService.release_button[i]
                else:
                    r_flag = r_flag + HIDService.release_button[i]
                j = j + 1

            if l_flag == 0:
                events.append(HIDService.crete_event("l_0", True))
            if r_flag == 0:
                events.append(HIDService.crete_event("r_0", True))
            if not HIDService.is_show_bg_l0:
                events.append(HIDService.crete_event("l_0", False))
            if not HIDService.is_show_bg_r0:
                events.append(HIDService.crete_event("r_0", False))
            return events

        except Exception as e:
            print(f"❌ 结构化数据处理错误: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def _get_key_mapping(byte_index, bit_position):
        """
        根据字节索引和位位置返回对应的按键名称
        这里需要你根据设备协议填写正确的映射
        """
        KEY_MAPPING = {

            LR: 'S',
            LG: 'A',
            LB: 'D',
            RR: 'W',
            RG: 'Space',
            RB: 'Enter',
            LW: 'Shift',
            RW: 'Ctrl',

        }

        return KEY_MAPPING.get((byte_index, bit_position))

    @staticmethod
    def get_sub_position(rotary0):
        total_range = 255
        sub_range_size = total_range / 20  # 3276.8
        sub_pos = int(rotary0 // sub_range_size)  # 映射到0~19
        return min(max(sub_pos, 0), 19)  # 限制在0~19

    @staticmethod
    def get_pos(position):
        pos_image = ""
        if L_MAX + 20 > position >= L_2:
            pos_image = "lever_-2"
        if L_2 > position >= L_1:
            pos_image = "lever_-1"
        if L_1 > position >= R_1:
            pos_image = "lever_0"
        if R_1 > position >= R_2:
            pos_image = "lever_1"
        if R_2 > position > R_MAX - 20:
            pos_image = "lever_2"
        return pos_image

    @staticmethod
    def crete_event(key, visible):
        event = {
            'key': key,
            'visible': visible,
        }
        return event
