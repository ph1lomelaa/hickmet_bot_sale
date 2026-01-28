import os
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime


class WebhookNotifier:
    

    def __init__(self):

        self.webhook_url = os.getenv("BOOKING_WEBHOOK_URL", "")
        self.enabled = bool(self.webhook_url)
        self.timeout = 10.0  # таймаут запроса в секундах

        if self.enabled:
            print(f"✅ Webhook уведомления включены: {self.webhook_url}")
        else:
            print("⚠️ Webhook уведомления отключены (BOOKING_WEBHOOK_URL не установлен)")

    async def send_booking_notification(
        self,
        bookings_data: List[Dict[str, Any]],
        package_info: Dict[str, Any],
        db_ids: List[int],
        saved_rows: List[int]
    ) -> bool:
        if not self.enabled:
            return False

        try:

            payload = {
                "event": "new_booking",
                "timestamp": datetime.now().isoformat(),
                "package": package_info,
                "pilgrims": bookings_data,
                "metadata": {
                    "total_pilgrims": len(bookings_data),
                    "db_ids": db_ids,
                    "sheet_rows": saved_rows
                }
            }

            print(f"\n📤 Отправка webhook уведомления...")
            print(f"   URL: {self.webhook_url}")
            print(f"   Паломников: {len(bookings_data)}")
            print(f"   Пакет: {package_info.get('name', 'N/A')}")

            # Отправляем POST запрос
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "BullBot-Webhook/1.0"
                    }
                )

                if response.status_code in [200, 201, 202, 204]:
                    print(f"✅ Webhook отправлен успешно (HTTP {response.status_code})")
                    return True
                else:
                    print(f"⚠️ Webhook вернул код {response.status_code}")
                    print(f"   Ответ: {response.text[:200]}")
                    return False

        except httpx.TimeoutException:
            print(f"❌ Timeout при отправке webhook (>{self.timeout}s)")
            return False
        except httpx.RequestError as e:
            print(f"❌ Ошибка при отправке webhook: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка webhook: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def send_test_notification(self) -> bool:
        
        if not self.enabled:
            print("❌ Webhook отключен, тестовое уведомление не отправлено")
            return False

        test_payload = {
            "event": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "Это тестовое уведомление от BullBot"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=test_payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "BullBot-Webhook/1.0"
                    }
                )

                if response.status_code in [200, 201, 202, 204]:
                    print(f"✅ Тестовый webhook отправлен успешно (HTTP {response.status_code})")
                    return True
                else:
                    print(f"⚠️ Тестовый webhook вернул код {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Ошибка при отправке тестового webhook: {e}")
            return False


webhook_notifier = WebhookNotifier()


async def notify_new_booking(
    bookings_data: List[Dict[str, Any]],
    package_name: str,
    sheet_name: str,
    table_id: str,
    db_ids: List[int],
    saved_rows: List[int]
) -> bool:
    package_info = {
        "name": package_name,
        "date": sheet_name,
        "table_id": table_id
    }

    return await webhook_notifier.send_booking_notification(
        bookings_data=bookings_data,
        package_info=package_info,
        db_ids=db_ids,
        saved_rows=saved_rows
    )
