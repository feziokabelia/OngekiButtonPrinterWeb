# OngekiButtonPrinterWeb
用于ongeki手台的Keyboard viewer  
![Assembly photo](pictures/krq6u-ovrwt.gif)

### 目前支持的手台：
IO4手台（my台，sim台等使用IO4的手台）  
Ontroller（dao台）  
Nageki  
### 计划中：
1.打包 ✅  
2.增加设置页面  
3.支持源台焊台
## 本地部署
### 环境
Python 3.10+
```bash
# 克隆项目到本地
git clone https://github.com/feziokabelia/OngekiButtonPrinterWeb.git
# 安装依赖
pip install -r requirements.txt
```
### 项目配置
  ```python
# Ongeki_helper_Web/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',  # 数据库名称
        'USER': '',  # MySQL 用户名
        'PASSWORD': '',  # ⭐ 修改为你的MySQL密码
        'HOST': 'localhost',  # 数据库主机
        'PORT': '3306',  # MySQL 端口
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}
  ```
### 建立数据库
  ```bash
  # 创建数据库表结构 
python manage.py migrate
# 导入按钮配置数据
python manage.py loaddata initial_data.json
  ```
应该也可以使用insert_buttons.py
  ```bash
  # 添加buttons_config表脚本
python insert_buttons.py
  ```
### 运行
  ```bash
daphne Ongeki_helper_Web.asgi:application --port 8000 --verbosity 2
  ```
```bash
python hid_reader.py
# 成功的话 http://127.0.0.1:8000/运行
```
### [注意]
该版本为Web版本，独立版本点[这里](https://github.com/feziokabelia/OngekiButtonPrinter)  

### 可以找主播定制小人儿啦，[b站私信](https://space.bilibili.com/4840504)  私信联系喵( ˘ ³˘)♥