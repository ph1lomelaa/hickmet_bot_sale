#!/usr/bin/env python3
"""
WebSocket клиент для получения уведомлений о новых телефонах.
Работает бесконечно до Ctrl+C.
"""
import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "wss://marxist-noell-uslima2005-12a246c3.koyeb.app/ws/phones"

async def listen_forever():
    print("=" * 70)
    print("📱 HICKMET TRAVEL - Phone Notifications Listener")
    print("=" * 70)
    print(f"🔌 Connecting to: {WS_URL}")
    print("⏳ Press Ctrl+C to stop")
    print("=" * 70)

    while True:  # Автоматический реконнект
        try:
            async with websockets.connect(WS_URL) as ws:
                print(f"\n✅ Connected at {datetime.now().strftime('%H:%M:%S')}")
                print("   Waiting for new phone numbers...")
                print("-" * 70)

                # Периодически отправляем ping
                async def send_ping():
                    while True:
                        await asyncio.sleep(20)
                        try:
                            await ws.send("ping")
                            print(f"🏓 Ping sent at {datetime.now().strftime('%H:%M:%S')}")
                        except:
                            break

                # Запускаем ping в фоне
                ping_task = asyncio.create_task(send_ping())

                try:
                    # Слушаем сообщения
                    while True:
                        message = await ws.recv()

                        # Игнорируем pong
                        if message == "pong":
                            continue

                        try:
                            data = json.loads(message)

                            if data.get("event") == "new_phone":
                                print(f"\n🎉 NEW PHONE RECEIVED!")
                                print(f"   📱 Phone:      {data['phone']}")
                                print(f"   👤 Guest:      {data['guest_name']}")
                                print(f"   🆔 Booking ID: {data['booking_id']}")
                                print(f"   🕐 Time:       {data['timestamp']}")
                                print("-" * 70)
                        except json.JSONDecodeError:
                            print(f"   ℹ️  Received: {message}")

                except websockets.exceptions.ConnectionClosed:
                    ping_task.cancel()
                    print(f"\n⚠️  Connection closed at {datetime.now().strftime('%H:%M:%S')}")
                    print("   Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)

        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(listen_forever())
    except KeyboardInterrupt:
        print("\n\n✅ Disconnected successfully")
