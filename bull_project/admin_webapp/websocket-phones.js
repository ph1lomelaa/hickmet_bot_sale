/**
 * WebSocket модуль для получения мгновенных уведомлений о новых телефонах
 * Использование:
 *
 * import { PhoneWebSocket } from './websocket-phones.js';
 *
 * const phoneWS = new PhoneWebSocket({
 *     onNewPhone: (data) => {
 *         console.log('Новый телефон:', data.phone);
 *     },
 *     autoReconnect: true
 * });
 */

class PhoneWebSocket {
    constructor(options = {}) {
        this.options = {
            url: options.url || this.getWebSocketUrl(),
            onNewPhone: options.onNewPhone || this.defaultOnNewPhone,
            onConnect: options.onConnect || (() => {}),
            onDisconnect: options.onDisconnect || (() => {}),
            onError: options.onError || ((error) => console.error('WebSocket error:', error)),
            autoReconnect: options.autoReconnect !== false,
            reconnectDelay: options.reconnectDelay || 3000,
            showNotifications: options.showNotifications !== false,
            playSound: options.playSound !== false
        };

        this.ws = null;
        this.isConnected = false;
        this.reconnectTimer = null;
        this.phoneHistory = []; // История полученных телефонов

        this.connect();
    }

    /**
     * Определяет URL WebSocket на основе текущего API_BASE_URL
     */
    getWebSocketUrl() {
        if (typeof API_BASE_URL !== 'undefined') {
            // Преобразуем HTTP URL в WebSocket URL
            const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
            const url = API_BASE_URL.replace(/^https?:\/\//, '');
            return `${wsProtocol}://${url}/ws/phones`;
        }
        // Fallback для локальной разработки
        return 'ws://localhost:8000/ws/phones';
    }

    /**
     * Подключение к WebSocket серверу
     */
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('📱 WebSocket уже подключен');
            return;
        }

        console.log('📱 Подключение к WebSocket:', this.options.url);

        try {
            this.ws = new WebSocket(this.options.url);

            this.ws.onopen = () => {
                console.log('✅ WebSocket подключен');
                this.isConnected = true;
                this.options.onConnect();

                // Очищаем таймер переподключения
                if (this.reconnectTimer) {
                    clearTimeout(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📥 Получено сообщение:', data);

                    if (data.event === 'new_phone') {
                        this.handleNewPhone(data);
                    }
                } catch (error) {
                    console.error('❌ Ошибка парсинга сообщения:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket ошибка:', error);
                this.options.onError(error);
            };

            this.ws.onclose = () => {
                console.log('❌ WebSocket отключен');
                this.isConnected = false;
                this.options.onDisconnect();

                // Автоматическое переподключение
                if (this.options.autoReconnect) {
                    console.log(`🔄 Переподключение через ${this.options.reconnectDelay}ms...`);
                    this.reconnectTimer = setTimeout(() => {
                        this.connect();
                    }, this.options.reconnectDelay);
                }
            };
        } catch (error) {
            console.error('❌ Ошибка создания WebSocket:', error);
            this.options.onError(error);
        }
    }

    /**
     * Обработка нового телефона
     */
    handleNewPhone(data) {
        // Добавляем в историю
        this.phoneHistory.unshift(data);

        // Ограничиваем размер истории (максимум 100 записей)
        if (this.phoneHistory.length > 100) {
            this.phoneHistory.pop();
        }

        // Вызываем callback
        this.options.onNewPhone(data);

        // Показываем browser notification
        if (this.options.showNotifications) {
            this.showBrowserNotification(data);
        }

        // Воспроизводим звук
        if (this.options.playSound) {
            this.playNotificationSound();
        }
    }

    /**
     * Показ браузерного уведомления
     */
    showBrowserNotification(data) {
        if (!("Notification" in window)) {
            return;
        }

        if (Notification.permission === "granted") {
            new Notification("📱 Новый телефон!", {
                body: `${data.phone}\n${data.guest_name}`,
                icon: "📱",
                tag: `phone-${data.booking_id}`, // Предотвращает дублирование
                requireInteraction: false
            });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    new Notification("📱 Новый телефон!", {
                        body: `${data.phone}\n${data.guest_name}`,
                        icon: "📱"
                    });
                }
            });
        }
    }

    /**
     * Воспроизведение звука уведомления
     */
    playNotificationSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.warn('⚠️ Не удалось воспроизвести звук:', error);
        }
    }

    /**
     * Дефолтный обработчик нового телефона
     */
    defaultOnNewPhone(data) {
        console.log('📱 НОВЫЙ ТЕЛЕФОН:', data.phone);
        console.log('   Гость:', data.guest_name);
        console.log('   ID брони:', data.booking_id);
        console.log('   Время:', new Date(data.timestamp).toLocaleString('ru-RU'));
    }

    /**
     * Отключение от WebSocket
     */
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
    }

    /**
     * Получение истории телефонов
     */
    getHistory() {
        return this.phoneHistory;
    }

    /**
     * Очистка истории
     */
    clearHistory() {
        this.phoneHistory = [];
    }

    /**
     * Статус подключения
     */
    getStatus() {
        return {
            connected: this.isConnected,
            url: this.options.url,
            historyCount: this.phoneHistory.length
        };
    }
}

// Export для использования в других файлах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PhoneWebSocket };
}
