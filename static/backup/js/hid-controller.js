// static/js/hid-controller.js
class HIDController {
    constructor() {
        this.socket = null;
        this.images = new Map();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.init();
    }

    /**
     * 初始化控制器
     */
    init() {
        console.log('🎮 HID 控制器初始化...');
        console.log('📊 按钮数据:', BUTTONS_DATA);
        console.log('🔗 WebSocket URL:', WEBSOCKET_URL);

        if (BUTTONS_DATA && BUTTONS_DATA.length > 0) {
            this.createButtonsFromDatabase();
        } else {
            console.error('❌ 没有可用的按钮数据');
        }

        this.setupWebSocket();
    }

    /**
     * 从数据库数据创建按钮图片
     */
    createButtonsFromDatabase() {
    console.log('🔄 开始创建按钮图片...');

    const buttonsContainer = document.getElementById('buttons-container');
    let createdCount = 0;

    BUTTONS_DATA.forEach((button, index) => {
        console.log(`  处理按钮 ${index + 1}/${BUTTONS_DATA.length}:`, button);

        if (!button.key) {
            console.warn('   ⚠️ 跳过没有 key 的按钮:', button);
            return;
        }

        if (!button.image_url) {
            console.warn('   ⚠️ 跳过没有 image_url 的按钮:', button);
            return;
        }

        const img = document.createElement('img');
        img.src = button.image_url;
        img.setAttribute('data-key', button.key);
        img.className = 'dynamic-button hidden';
        img.alt = button.image_name || button.key;

        // 所有按钮都覆盖在相同位置，与背景图片重叠
        // 不需要设置具体位置，因为 CSS 已经定义了绝对定位和全尺寸

        // 添加到容器
        buttonsContainer.appendChild(img);

        // 存储到映射中
        this.images.set(button.key, img);
        createdCount++;

        console.log(`   ✅ 创建叠加按钮: ${button.key}`);
    });

    console.log(`🎯 成功创建 ${createdCount} 个叠加按钮图片`);
}



    /**
     * 建立 WebSocket 连接
     */
   setupWebSocket() {
    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}${WEBSOCKET_URL}`;

        console.log(`🔗 尝试连接 WebSocket: ${wsUrl}`);

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (event) => {
            console.log('✅ WebSocket 连接已建立');
            console.log('📡 现在可以接收后端发送的数据了');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);

            // 发送一个测试消息确认双向通信
            this.sendTestMessage();
        };

        this.socket.onmessage = (event) => {
            console.log('='.repeat(60));
            console.log('📨 📨 📨 收到 WebSocket 消息 📨 📨 📨');
            console.log('='.repeat(60));
            console.log('📦 原始消息内容:', event.data);
            console.log('📦 消息类型:', typeof event.data);

            try {
                const data = JSON.parse(event.data);
                console.log('✅ JSON 解析成功');
                console.log('📊 解析后的数据:', data);
                this.handleMessage(data);
            } catch (error) {
                console.error('❌ JSON 解析失败:', error);
                console.error('❌ 原始数据:', event.data);
            }

            console.log('='.repeat(60));
        };

        this.socket.onclose = (event) => {
            console.log('🔌 WebSocket 连接已关闭:', event.code, event.reason);
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.handleReconnection();
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket 错误:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        };

    } catch (error) {
        console.error('❌ 创建 WebSocket 连接失败:', error);
    }
}
    /**
     * 发送测试消息确认通信
     */
    sendTestMessage() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const testMessage = {
                type: 'ping',
                message: '前端测试消息',
                timestamp: Date.now()
            };
            this.socket.send(JSON.stringify(testMessage));
            console.log('📤 发送测试消息:', testMessage);
        }
    }

    /**
     * 处理重连逻辑
     */
    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * this.reconnectAttempts, 10000);

            console.log(`🔄 ${this.reconnectAttempts}/${this.maxReconnectAttempts} 尝试重新连接...`);

            setTimeout(() => {
                this.setupWebSocket();
            }, delay);
        } else {
            console.error('💥 达到最大重连次数，停止重连');
        }
    }

    /**
     * 处理来自服务器的消息
     */
    handleMessage(data) {
        console.log('🔄 开始处理消息...');
        console.log('📋 消息结构:', data);

        if (!data) {
            console.error('❌ 消息数据为空');
            return;
        }

        console.log(`📊 消息类型: ${data.type}`);
        console.log(`📊 消息键名:`, Object.keys(data));

        switch(data.type) {
            case 'batch_display_update':
                console.log(`🎯 收到显示状态更新，包含 ${data.total_events} 个事件`);
                console.log('📋 事件列表:', data.events);

                if (data.events && Array.isArray(data.events)) {
                    data.events.forEach((event, index) => {
                        console.log(`   ${index + 1}. key: "${event.key}", visible: ${event.visible}`);
                    });
                }

                this.updateDisplay(data.events);
                break;

            case 'processing_result':
                console.log('💡 处理结果消息:', data.message);
                console.log('📊 完整数据:', data);
                this.showNotification(data.message);
                break;

            case 'error':
                console.error('❌ 错误消息:', data.message);
                console.error('📊 完整错误数据:', data);
                this.showError(data.message);
                break;

            default:
                console.warn('⚠️ 未知消息类型:', data.type);
                console.warn('📊 完整消息数据:', data);
        }

        console.log('✅ 消息处理完成');
    }

    /**
     * 更新图片显示状态
     */
    updateDisplay(events) {
        console.log('🔄 开始更新显示状态...');

        if (!events) {
            console.error('❌ events 参数为 undefined 或 null');
            return;
        }

        if (!Array.isArray(events)) {
            console.error('❌ events 不是数组，实际类型:', typeof events);
            console.error('❌ events 值:', events);
            return;
        }

        // console.log(`📊 需要更新 ${events.length} 个按钮`);

        if (events.length === 0) {
            console.warn('⚠️ 事件列表为空，没有需要更新的按钮');
            return;
        }

        let successCount = 0;
        let failCount = 0;

        events.forEach((event, index) => {
            console.log(`  处理第 ${index + 1} 个事件:`, event);

            const { key, visible } = event;

            if (!key) {
                console.warn(`   ⚠️ 跳过没有 key 的事件:`, event);
                failCount++;
                return;
            }

            const imageElement = this.images.get(key);

            if (imageElement) {
                if (visible) {
                    imageElement.classList.remove('hidden');
                    imageElement.classList.add('visible');
                    console.log(`   ✅ 显示按钮: ${key}`);
                } else {
                    imageElement.classList.remove('visible');
                    imageElement.classList.add('hidden');
                    console.log(`   ❌ 隐藏按钮: ${key}`);
                }
                successCount++;
            } else {
                console.warn(`   ⚠️ 未找到对应的图片元素: ${key}`);
                failCount++;
            }
        });

        console.log(`🎯 更新完成: ${successCount} 个成功, ${failCount} 个失败`);
    }

    /**
     * 更新连接状态显示
     */
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('status');
        if (!statusElement) return;

        if (connected) {
            statusElement.textContent = '已连接';
            statusElement.className = 'status connected';
        } else {
            statusElement.textContent = '断开连接';
            statusElement.className = 'status disconnected';
        }
    }

    /**
     * 显示通知
     */
    showNotification(message) {
        console.log('💡 通知:', message);
        // 可以在这里添加 UI 通知
    }

    /**
     * 显示错误
     */
    showError(message) {
        console.error('❌ 错误:', message);
        // 可以在这里添加 UI 错误提示
    }

    /**
     * 销毁控制器（清理资源）
     */
    destroy() {
        if (this.socket) {
            this.socket.close();
        }
        this.images.clear();
        console.log('🧹 HID 控制器已销毁');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 页面加载完成，开始初始化 HID 控制器');
    window.hidController = new HIDController();
});

// 页面卸载前清理资源
window.addEventListener('beforeunload', () => {
    if (window.hidController) {
        window.hidController.destroy();
    }
});