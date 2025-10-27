# button_printer/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import HIDService


@csrf_exempt
def hid_data_receiver(request):
    """
    接收 HID 数据的 API 接口
    期望的 JSON 数据格式:
    {
        "unpacked": [ ... ],  # HIDAPI 解析后的数据
        "device_id": "device_001"
    }
    """
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            unpacked_data = data.get('unpacked', [])

            if not unpacked_data:
                return JsonResponse({'error': '缺少HID数据'}, status=400)

            # 调用服务层处理 HID 数据
            events = HIDService.process_hid_data(unpacked_data)

            # 处理每个事件
            results = []
            for event in events:
                result = HIDService.handle_hid_event(event)
                results.append(result)

            return JsonResponse({
                'status': 'success',
                'processed_events': len(events),
                'actions': results
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': '只支持POST请求'}, status=405)