# hid_app/views.py
import json

from django.shortcuts import render
from django.http import JsonResponse
from .models import ButtonConfig


def index(request):
    """主页面 - 从数据库获取所有按钮配置"""
    try:
        # 从数据库获取所有按钮配置
        button_configs = ButtonConfig.objects.all()

        print(f"🎯 数据库查询到 {button_configs.count()} 条记录")

        # 转换为前端需要的格式
        buttons_data = []
        for i, config in enumerate(button_configs):
            button_info = {
                'key': config.button_key,
                'image_url': config.full_image_path,
                'image_name': config.image_name
            }
            buttons_data.append(button_info)
            if i < 5:  # 只打印前5条避免太多输出
                print(f"🔘 [{i}] 按钮: {config.button_key} -> {config.full_image_path}")

        # 将数据转换为 JSON 字符串
        buttons_data_json = json.dumps(buttons_data, ensure_ascii=False)

        # print(f"📊 JSON 字符串长度: {len(buttons_data_json)}")
        # print(f"📊 JSON 数据类型: {type(buttons_data_json)}")
        # print(f"📊 JSON 前200字符: {buttons_data_json[:200]}")

        context = {
            'title': 'OngekiButtonPrinterWeb',
            'version': '1.0.0',
            'buttons_data_json': buttons_data_json,
            'websocket_url': '/ws/hid/'
        }

        print("✅ 上下文数据准备完成")

    except Exception as e:
        print(f"❌ 加载按钮配置失败: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'title': 'OngekiButtonPrinterWeb',
            'version': '1.0.0',
            'buttons_data_json': '[]',
            'websocket_url': '/ws/hid/'
        }

    return render(request, 'button_printer/index.html', context)


def get_button_configs_api(request):
    """API接口：获取所有按钮配置（JSON格式）"""
    try:
        button_configs = ButtonConfig.objects.all()
        buttons_data = []

        for config in button_configs:
            buttons_data.append({
                'key': config.button_key,
                'image_url': config.full_image_path,
                'image_name': config.image_name
            })

        return JsonResponse({
            'status': 'success',
            'buttons': buttons_data,
            'count': len(buttons_data)
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)