#!/usr/bin/env python3
"""
Скрипт для отправки тестового webhook уведомления
Показывает какие данные отправляются другому человеку при создании брони
"""

import httpx
import asyncio
from datetime import datetime
import json

# URL куда отправляем (наш локальный тестовый сервер)
WEBHOOK_URL = "http://localhost:9000/webhook"

# Тестовые данные брони (такие же как отправляются в реальности)
test_booking_data = {
    "event": "new_booking",
    "timestamp": datetime.now().isoformat(),
    "package": {
        "name": "Умра 25-Янв (ТЕСТ)",
        "date": "25.01.2025",
        "table_id": "1abc123def456"
    },
    "pilgrims": [
        {
            "table_id": "1abc123def456",
            "sheet_name": "JAN 25.01",
            "sheet_row_number": 42,
            "package_name": "Умра 25-Янв (ТЕСТ)",
            "guest_last_name": "Тестов",
            "guest_first_name": "Тест",
            "gender": "M",
            "date_of_birth": "01.01.1990",
            "passport_num": "N12345678",
            "passport_expiry": "01.01.2030",
            "guest_iin": "900101123456",
            "client_phone": "+77001234567",
            "room_type": "Double",
            "meal_type": "HB",
            "price": "1500",
            "amount_paid": "500",
            "manager_name_text": "Менеджер Тест",
            "region": "Almaty",
            "departure_city": "Almaty",
            "source": "Telegram Bot",
            "visa_status": "UMRAH VISA",
            "avia": "Требуется",
            "train": "-",
            "comment": "Тестовая бронь для проверки webhook",
            "passport_image_path": "/passports/test_passport.jpg",
            "passport_warning": None,
            "status": "new",
            "group_members": ["Тестов Тест", "Петрова Анна"],
            "is_infant": False,
            "is_child": False,
            "contract_number": "Contract-123",
            "exchange_rate": "495",
            "discount": "-"
        },
        {
            "table_id": "1abc123def456",
            "sheet_name": "JAN 25.01",
            "sheet_row_number": 43,
            "package_name": "Умра 25-Янв (ТЕСТ)",
            "guest_last_name": "Петрова",
            "guest_first_name": "Анна",
            "gender": "F",
            "date_of_birth": "15.03.1992",
            "passport_num": "N98765432",
            "passport_expiry": "15.03.2032",
            "guest_iin": "920315654321",
            "client_phone": "+77009876543",
            "room_type": "Double",
            "meal_type": "HB",
            "price": "1500",
            "amount_paid": "750",
            "manager_name_text": "Менеджер Тест",
            "region": "Almaty",
            "departure_city": "Almaty",
            "source": "Telegram Bot",
            "visa_status": "UMRAH VISA",
            "avia": "Требуется",
            "train": "-",
            "comment": "Тестовая бронь для проверки webhook",
            "passport_image_path": "/passports/test_passport2.jpg",
            "passport_warning": None,
            "status": "new",
            "group_members": ["Тестов Тест", "Петрова Анна"],
            "is_infant": False,
            "is_child": False,
            "contract_number": "Contract-123",
            "exchange_rate": "495",
            "discount": "-"
        }
    ],
    "metadata": {
        "total_pilgrims": 2,
        "db_ids": [999, 1000],
        "sheet_rows": [42, 43]
    }
}


async def send_webhook():
    """
    Отправляет тестовый webhook
    """
    print("\n" + "="*70)
    print("📤 ОТПРАВКА ТЕСТОВОГО WEBHOOK")
    print("="*70)
    print(f"🔗 URL: {WEBHOOK_URL}")
    print(f"📦 Пакет: {test_booking_data['package']['name']}")
    print(f"👥 Паломников: {len(test_booking_data['pilgrims'])}")
    print()
    print("📋 Данные которые будут отправлены:")
    print("-" * 70)
    print(json.dumps(test_booking_data, ensure_ascii=False, indent=2))
    print("-" * 70)
    print()
    print("⏳ Отправляю...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                WEBHOOK_URL,
                json=test_booking_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "BullBot-Webhook-Test/1.0"
                }
            )

            if response.status_code in [200, 201, 202, 204]:
                print(f"\n✅ SUCCESS! Webhook отправлен успешно")
                print(f"📊 HTTP статус: {response.status_code}")
                print(f"\n📥 Ответ от сервера:")
                try:
                    response_data = response.json()
                    print(json.dumps(response_data, ensure_ascii=False, indent=2))
                except:
                    print(response.text)
            else:
                print(f"\n⚠️  WARNING: Неожиданный статус код")
                print(f"📊 HTTP статус: {response.status_code}")
                print(f"📄 Ответ: {response.text}")

    except httpx.TimeoutException:
        print(f"\n❌ ERROR: Timeout (сервер не ответил за 10 секунд)")
    except httpx.ConnectError:
        print(f"\n❌ ERROR: Не удалось подключиться к {WEBHOOK_URL}")
        print(f"\nПроверьте что тестовый сервер запущен:")
        print(f"  python test_webhook_receiver.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print()


if __name__ == "__main__":
    print("\n🧪 Тестовый скрипт для отправки webhook уведомлений\n")
    asyncio.run(send_webhook())
