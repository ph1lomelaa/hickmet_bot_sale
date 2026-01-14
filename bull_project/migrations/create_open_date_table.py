"""
Миграция для создания таблицы open_date_bookings

Использование:
    python migrations/create_open_date_table.py
"""

import asyncio
from sqlalchemy import text
from bull_project.bull_bot.database.setup import engine


async def create_open_date_table():
    """Создает таблицу open_date_bookings"""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS open_date_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manager_id BIGINT NOT NULL,
        manager_name_text VARCHAR,

        pilgrim_data TEXT,  -- JSON массив

        room_type VARCHAR,
        meal_type VARCHAR,
        price VARCHAR,
        region VARCHAR,
        departure_city VARCHAR,

        client_phone VARCHAR NOT NULL,
        comment TEXT,

        google_sheet_row INTEGER,

        status VARCHAR DEFAULT 'OPEN',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (manager_id) REFERENCES users (telegram_id)
    )
    """

    try:
        async with engine.begin() as conn:
            await conn.execute(text(create_table_sql))
            print("✅ Таблица open_date_bookings успешно создана!")

    except Exception as e:
        print(f"❌ Ошибка при создании таблицы: {e}")
        if "already exists" in str(e).lower():
            print("ℹ️ Таблица уже существует, миграция не требуется")
        else:
            raise


if __name__ == "__main__":
    print("🔄 Запуск миграции для создания таблицы open_date_bookings...")
    asyncio.run(create_open_date_table())
    print("✅ Миграция завершена!")
