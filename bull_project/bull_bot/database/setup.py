import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from .models import Base

# Находим корень проекта, чтобы путь был всегда верным
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bull_database.db")

# Берем URL из переменной окружения, по умолчанию используем локальный SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")
print(f"🔍 DEBUG setup.py: os.getenv('DATABASE_URL') = {os.getenv('DATABASE_URL')}")
print(f"🔍 DEBUG setup.py: DATABASE_URL итоговый = {DATABASE_URL}")

# Автоматически конвертируем postgresql:// в postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Поднимаем пул с pre_ping и recyclе, чтобы чинить отвалившиеся коннекты
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,  # 30 минут
)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    """Создает таблицы, если их нет. Вызывать при старте main.py и api_server.py"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Безопасная миграция: добавляем group_members если её нет
        if DATABASE_URL.startswith("postgresql"):
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='bookings' AND column_name='group_members'
                    ) THEN
                        ALTER TABLE bookings ADD COLUMN group_members JSONB;
                        RAISE NOTICE 'Колонка group_members добавлена';
                    ELSE
                        RAISE NOTICE 'Колонка group_members уже существует';
                    END IF;
                END $$;
            """))
            print("   ℹ️ Миграция group_members выполнена")
        elif "sqlite" in DATABASE_URL:
            # Для SQLite проверяем через pragma
            try:
                result = await conn.execute(text("PRAGMA table_info(bookings)"))
                columns = [row[1] for row in result.fetchall()]
                if 'group_members' not in columns:
                    await conn.execute(text("ALTER TABLE bookings ADD COLUMN group_members TEXT"))
                    print("   ℹ️ Колонка group_members добавлена")
                else:
                    print("   ℹ️ Колонка group_members уже существует")
            except Exception as e:
                print(f"   ⚠️ Не удалось проверить/добавить group_members: {e}")

    print(f"✅ База данных инициализирована по адресу: {DATABASE_URL}")
