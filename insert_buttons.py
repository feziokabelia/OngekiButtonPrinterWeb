# insert_buttons.py - 放在项目根目录
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ongeki_helper_Web.settings')
django.setup()

from button_printer.models import ButtonConfig

# 31 0 5 4 | 1 16 15 14 ←从左到右是左侧键到右侧键
LW = "31"
LR = "0"
LG = "5"
LB = "4"

RR = "1"
RG = "16"
RB = "15"
RW = "14"


def main():
    """插入按钮数据"""

    # 按钮配置数据
    button_configs = [
        (LW, '1_on.png'),
        (LW + "m", '1.png'),

        (LR, '2_on.png'),
        (LR + "m", '2.png'),

        (LG, '3_on.png'),
        (LG + "m", '3.png'),

        (LB, '4_on.png'),
        (LB + "m", '4.png'),

        (RR, '5_on.png'),
        (RR + "m", '5.png'),

        (RG, '6_on.png'),
        (RG + "m", '6.png'),

        (RB, '7_on.png'),
        (RB + "m", '7.png'),

        (RW, '7_on.png'),
        (RW + "m", '7.png'),

        ('l_lever_0', 'l_swing_0.png'),
        ('l_lever_1', 'l_swing_1.png'),
        ('l_lever_2', 'l_swing_2.png'),
        ('l_lever_-1', 'l_swing_-1.png'),
        ('l_lever_-2', 'l_swing_-2.png'),

        ('r_lever_0', 'r_swing_0.png'),
        ('r_lever_1', 'r_swing_1.png'),
        ('r_lever_2', 'r_swing_2.png'),
        ('r_lever_-1', 'r_swing_-1.png'),
        ('r_lever_-2', 'r_swing_-2.png'),

        ('lever_0', 'swing_0.png'),
        ('lever_1', 'swing_1.png'),
        ('lever_2', 'swing_2.png'),
        ('lever_-1', 'swing_-1.png'),
        ('lever_-2', 'swing_-2.png'),

        ('bg_swing', 'swing.png'),
        ('l_0', 'l_0.png'),
        ('r_0', 'r_0.png'),
    ]

    print("开始插入按钮数据...")

    for key, image in button_configs:
        button, created = ButtonConfig.objects.get_or_create(
            button_key=key,
            defaults={'image_name': image}
        )
        status = "✅ 创建" if created else "⚠️ 已存在"
        print(f"{status}: {key} -> {image}")

    print("数据插入完成！")


if __name__ == "__main__":
    main()
