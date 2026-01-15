

(function() {
    'use strict';

    let phoneWS = null;
    let phoneNotificationBadge = null;
    function initPhoneWebSocket() {
        console.log('🚀 Инициализация WebSocket для телефонов...');

        phoneWS = new PhoneWebSocket({
            onNewPhone: handleNewPhone,
            onConnect: handleConnect,
            onDisconnect: handleDisconnect,
            autoReconnect: true,
            showNotifications: true,
            playSound: true
        });

        createNotificationBadge();
        requestNotificationPermission();
    }

    function handleNewPhone(data) {
        console.log('📱 Новый телефон получен:', data);

        // Показываем всплывающее уведомление на странице
        showPageNotification(data);

        // Обновляем badge счетчика
        updateNotificationBadge();

        // Если страница сейчас показывает список броней - обновляем его
        refreshBookingsList();
    }

    /**
     * Создание badge для отображения счетчика новых телефонов
     */
    function createNotificationBadge() {
        // Создаем badge в шапке страницы
        phoneNotificationBadge = document.createElement('div');
        phoneNotificationBadge.id = 'phone-notification-badge';
        phoneNotificationBadge.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
            font-size: 14px;
            font-weight: 600;
            z-index: 9999;
            display: none;
            cursor: pointer;
            transition: all 0.3s ease;
        `;
        phoneNotificationBadge.innerHTML = `
            <span style="margin-right: 8px;">📱</span>
            <span id="phone-count">0</span> новых телефонов
        `;

        phoneNotificationBadge.addEventListener('click', () => {
            showPhoneHistory();
        });

        phoneNotificationBadge.addEventListener('mouseenter', () => {
            phoneNotificationBadge.style.transform = 'scale(1.05)';
        });

        phoneNotificationBadge.addEventListener('mouseleave', () => {
            phoneNotificationBadge.style.transform = 'scale(1)';
        });

        document.body.appendChild(phoneNotificationBadge);
    }

    /**
     * Обновление badge счетчика
     */
    function updateNotificationBadge() {
        const history = phoneWS.getHistory();
        const countElement = document.getElementById('phone-count');

        if (history.length > 0) {
            phoneNotificationBadge.style.display = 'block';
            if (countElement) {
                countElement.textContent = history.length;
            }
        }
    }

    /**
     * Показ истории телефонов в модальном окне
     */
    function showPhoneHistory() {
        const history = phoneWS.getHistory();

        if (history.length === 0) {
            alert('Нет новых телефонов');
            return;
        }

        // Создаем модальное окно
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        `;

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #3D3935;">📱 Новые телефоны</h2>
                <button onclick="this.closest('[style*=fixed]').remove(); phoneWS.clearHistory(); updateNotificationBadge();"
                        style="background: #E8E3DC; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer;">
                    Очистить все
                </button>
            </div>
        `;

        history.forEach((data, index) => {
            const time = new Date(data.timestamp).toLocaleString('ru-RU');
            html += `
                <div style="
                    background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
                    padding: 15px;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    border-left: 4px solid #2E7D32;
                ">
                    <div style="font-size: 18px; font-weight: bold; color: #2E7D32; margin-bottom: 5px;">
                        📞 ${data.phone}
                    </div>
                    <div style="color: #666; margin-bottom: 5px;">
                        👤 ${data.guest_name}
                    </div>
                    <div style="font-size: 12px; color: #999;">
                        🕐 ${time} | ID: ${data.booking_id}
                    </div>
                    <button onclick="copyToClipboard('${data.phone}')"
                            style="margin-top: 10px; background: #2E7D32; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">
                        Копировать телефон
                    </button>
                </div>
            `;
        });

        content.innerHTML = html;
        modal.appendChild(content);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
    }

    /**
     * Показ всплывающего уведомления на странице
     */
    function showPageNotification(data) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
            color: white;
            padding: 20px 25px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(46, 125, 50, 0.4);
            z-index: 9998;
            max-width: 350px;
            animation: slideInRight 0.4s ease-out;
        `;

        notification.innerHTML = `
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">
                📱 Новый телефон!
            </div>
            <div style="font-size: 20px; font-weight: bold; margin-bottom: 5px;">
                ${data.phone}
            </div>
            <div style="font-size: 14px; opacity: 0.95; margin-bottom: 8px;">
                👤 ${data.guest_name}
            </div>
            <div style="font-size: 12px; opacity: 0.85;">
                🕐 ${new Date(data.timestamp).toLocaleTimeString('ru-RU')}
            </div>
        `;

        // Добавляем анимацию
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(notification);

        // Клик для копирования телефона
        notification.addEventListener('click', () => {
            copyToClipboard(data.phone);
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        });

        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    /**
     * Копирование в буфер обмена
     */
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('✅ Телефон скопирован: ' + text);
        }).catch(err => {
            console.error('Ошибка копирования:', err);
            showToast('❌ Не удалось скопировать');
        });
    };

    /**
     * Показ toast уведомления
     */
    function showToast(message) {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10001;
            font-size: 14px;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 2000);
    }

    /**
     * Обновление списка броней
     */
    function refreshBookingsList() {
        // Проверяем, есть ли функция loadBookings
        if (typeof loadBookings === 'function') {
            console.log('🔄 Обновляем список броней...');
            // Не обновляем автоматически, чтобы не сбрасывать фильтры
            // Пользователь может обновить вручную
        }
    }

    /**
     * Обработка подключения
     */
    function handleConnect() {
        console.log('✅ WebSocket подключен');
        updateConnectionStatus(true);
    }

    /**
     * Обработка отключения
     */
    function handleDisconnect() {
        console.log('❌ WebSocket отключен');
        updateConnectionStatus(false);
    }

    /**
     * Обновление индикатора подключения
     */
    function updateConnectionStatus(connected) {
        let indicator = document.getElementById('ws-connection-indicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'ws-connection-indicator';
            indicator.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                z-index: 9999;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            `;
            document.body.appendChild(indicator);
        }

        if (connected) {
            indicator.style.background = '#4CAF50';
            indicator.title = '📱 WebSocket подключен - получаем уведомления в реальном времени';
        } else {
            indicator.style.background = '#F44336';
            indicator.title = '❌ WebSocket отключен - переподключение...';
        }
    }

    /**
     * Запрос разрешения на уведомления
     */
    function requestNotificationPermission() {
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission().then(permission => {
                console.log('Разрешение на уведомления:', permission);
            });
        }
    }

    // Инициализация при загрузке страницы
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPhoneWebSocket);
    } else {
        initPhoneWebSocket();
    }

    // Отключаемся при закрытии страницы
    window.addEventListener('beforeunload', () => {
        if (phoneWS) {
            phoneWS.disconnect();
        }
    });

    // Делаем доступными глобально для отладки
    window.phoneWS = phoneWS;
    window.updateNotificationBadge = updateNotificationBadge;

})();
