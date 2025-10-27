# test_db.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ongeki_helper_Web.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("✅ 数据库连接成功!")
        print(f"测试结果: {result}")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")