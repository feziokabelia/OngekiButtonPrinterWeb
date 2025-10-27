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
        console.log('🎮 OngekiButtonprinter初始化...');
        console.log('📊 按钮数据:', BUTTONS_DATA);
        console.log('🔗 WebSocket URL:', WEBSOCKET_URL);
        this.applyPerformanceCSS();

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
        //  console.log(`  处理按钮 ${index + 1}/${BUTTONS_DATA.length}:`, button);

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
        const swing = ["lever_-1", "lever_-2", "lever_0", "lever_1", "lever_2", ]
        const swingSet = new Set(swing)
        if (swingSet.has(button.key)){
            img.classList.add('z-swing')
        }
        else {img.classList.add('z-buttons')}




        // 所有按钮都覆盖在相同位置，与背景图片重叠
        // 不需要设置具体位置，因为 CSS 已经定义了绝对定位和全尺寸

        // 添加到容器
        buttonsContainer.appendChild(img);

        // 存储到映射中
        this.images.set(button.key, img);
        createdCount++;
        // console.log(`   ✅ 创建叠加按钮: ${button.key}`);
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

        // 使用二进制传输（如果可能）
        this.socket = new WebSocket(wsUrl);

        // 设置高优先级
        if (this.socket.setPriority) {
            this.socket.setPriority('high');
        }

        this.socket.binaryType = 'arraybuffer'; // 使用二进制传输

        this.socket.onopen = (event) => {
            console.log('✅ WebSocket 连接已建立');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            // this.updateConnectionStatus(true);

            // 发送性能配置
            const config = {
                type: 'performance_config',
                high_priority: true,
                timestamp: Date.now()
            };
            this.socket.send(JSON.stringify(config));
        };

        this.socket.onmessage = (event) => {
            // 立即处理，不等待
            const startTime = performance.now();

            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('❌ JSON 解析失败:', error);
            }

            const endTime = performance.now();
            if (endTime - startTime > 16) { // 超过一帧的时间
                console.warn('⚠️ 消息处理耗时:', endTime - startTime, 'ms');
            }
        };

        // ... 其他事件处理 ...
    } catch (error) {
        console.error('❌ 创建 WebSocket 连接失败:', error);
    }
}

    /**
     * 处理来自服务器的消息
     */
    handleMessage(data) {
        const startTime = performance.now();
        // 立即处理，不等待

        if (data.type === 'batch_display_update') {
            this.processDisplayUpdateImmediately(data.events);
        }

        const processTime = performance.now() - startTime;
        if (processTime > 10) {
            console.warn(`⚠️ 消息处理耗时: ${processTime.toFixed(2)}ms`);
        }
    }

/**
     * 立即处理显示更新
     */
    processDisplayUpdateImmediately(events) {
        if (!events || !Array.isArray(events)) return;
        // console.log("✅  接受到hid_reader信息")
        // 使用微任务确保同步执行
        const firstimageContainer = document.getElementById('first-image-container');
            firstimageContainer.classList.add('first-display');
        Promise.resolve().then(() => {
            for (const event of events) {
                const { key, visible } = event;
                if (!key) continue;
                const imageElement = this.images.get(key);
                if (!imageElement) continue;

                // 立即更新显示状态，无过渡效果
                if (visible) {

                    imageElement.classList.remove('hidden');
                    imageElement.classList.add('visible');
                } else {
                    imageElement.classList.remove('visible');
                    imageElement.classList.add('hidden');
                }
            }

            // 强制同步重绘
            this.forceSyncReflow();
        });
    }

    /**
     * 强制同步重绘
     */
    forceSyncReflow() {
        // 触发同步布局计算
        document.body.offsetHeight;
    }

    /**
     * 应用高性能 CSS
     */
    applyPerformanceCSS() {
        const style = document.createElement('style');
        style.textContent = `
            .dynamic-button {
                transition: none !important;
                will-change: opacity;
                backface-visibility: hidden;
                transform: translateZ(0);
            }
            .dynamic-button.hidden {
                opacity: 0;
                display: block !important;
            }
            .dynamic-button.visible {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 页面加载完成，开始初始化 OngekiButtonprinter');
    window.hidController = new HIDController();
});

// 页面卸载前清理资源
window.addEventListener('beforeunload', () => {
    if (window.hidController) {
        window.hidController.destroy();
    }
});