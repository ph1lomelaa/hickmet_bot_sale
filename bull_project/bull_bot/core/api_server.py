import os
import json
from datetime import datetime, timedelta
from urllib.parse import unquote_plus
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

# Импорты вашего проекта
from bull_project.bull_bot.core.smart_search import get_packages_by_date
from bull_project.bull_bot.core.google_sheets.allocator import get_open_rooms_for_manual_selection
from bull_project.bull_bot.core.google_sheets.client import (
    get_google_client,
    get_sheet_data,
    get_accessible_tables,
    get_sheet_names,
    get_packages_from_sheet,
)
from bull_project.bull_bot.core.google_sheets.writer import save_group_booking
from bull_project.bull_bot.database.setup import init_db
from bull_project.bull_bot.database.requests import (
    add_booking_to_db,
    update_booking_row,
    add_user,
)
from bull_project.bull_bot.core.parsers.passport_parser import PassportParserEasyOCR as PassportParser
from bull_project.bull_bot.core.parsers.pdf_generator import PassportPDFGenerator
# from bull_project.bull_bot.core.webhook_notifier import notify_new_booking  # Временно отключено
from bull_project.bull_bot.database.requests import (
    get_last_n_bookings_by_manager,
    get_booking_by_id,
    mark_booking_cancelled,
    get_full_analytics,
    get_manager_detailed_stats,
    search_packages_by_date,
    get_all_managers_list,
    get_all_bookings_for_period,
    search_tourist_by_name,
    get_db_packages_list,
    get_all_bookings_in_package,
    booking_exists,
    delete_bookings_by_ids
)
from bull_project.bull_bot.database.requests import (
    get_latest_passport_for_person,
    update_booking_fields,
    update_booking_passport_path,
    get_pending_requests,
    get_approval_request,
    update_approval_status,
    create_approval_request,
    mark_booking_rescheduled
)
from bull_project.bull_bot.core.google_sheets.writer import (
    clear_booking_in_sheets,
    write_cancelled_booking_red,
    write_rescheduled_booking_red,
    save_group_booking
)
from bull_project.bull_bot.config.constants import ABS_UPLOADS_DIR
from bull_project.bull_bot.core.passport_storage import resolve_passport_file_path
from bull_project.bull_bot.api.routes.rooms import router as rooms_router
from bull_project.bull_bot.api.routes.admin_requests import router as admin_requests_router
from bull_project.bull_bot.api.routes.open_date import router as open_date_router
from bull_project.bull_bot.core.websocket_manager import (
    phone_subscribers,
    admin_request_subscribers,
    notify_phone_subscribers,
    notify_admin_request_subscribers,
    notify_admins_about_request,
)
# uploads dir is shared via volume on API service
os.makedirs(ABS_UPLOADS_DIR, exist_ok=True)
# Инициализация парсера паспортов
passport_parser = PassportParser(debug=False)

# -----------------------------------------------------------------------------
# FASTAPI НАСТРОЙКА
# -----------------------------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],  # ← ВАЖНО для скачивания файлов!
)

app.include_router(rooms_router)
app.include_router(admin_requests_router)
app.include_router(open_date_router)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARE_WEBAPP_DIR = os.path.join(PROJECT_ROOT, "care_webapp")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Инициализация БД при старте приложения
@app.on_event("startup")
async def startup_event():
    await init_db()

# -----------------------------------------------------------------------------
# WEBSOCKET: Мгновенные уведомления о новых телефонах
# -----------------------------------------------------------------------------
@app.websocket("/ws/phones")
async def websocket_phone_updates(websocket: WebSocket):
    """WebSocket endpoint - клиенты подключаются сюда для получения новых телефонов мгновенно"""
    await websocket.accept()
    phone_subscribers.append(websocket)
    print(f"📱 WebSocket клиент подключен. Всего подписчиков: {len(phone_subscribers)}")
    try:
        while True:
            # Держим соединение открытым
            await websocket.receive_text()
    except WebSocketDisconnect:
        phone_subscribers.remove(websocket)
        print(f"📱 WebSocket клиент отключился. Всего подписчиков: {len(phone_subscribers)}")

# -----------------------------------------------------------------------------
# WEBSOCKET: Уведомления админов о новых заявках на отмену/перенос
# -----------------------------------------------------------------------------
@app.websocket("/ws/admin-requests")
async def websocket_admin_requests(websocket: WebSocket):
    """WebSocket endpoint - админы подключаются для получения уведомлений о заявках"""
    await websocket.accept()
    admin_request_subscribers.append(websocket)
    print(f"🔔 WebSocket админ подключен. Всего подписчиков: {len(admin_request_subscribers)}")
    try:
        while True:
            # Держим соединение открытым
            await websocket.receive_text()
    except WebSocketDisconnect:
        admin_request_subscribers.remove(websocket)
        print(f"🔔 WebSocket админ отключился. Всего подписчиков: {len(admin_request_subscribers)}")

# -----------------------------------------------------------------------------
# СТАТИЧЕСКИЕ ФАЙЛЫ
# -----------------------------------------------------------------------------
if os.path.isdir(CARE_WEBAPP_DIR):
    app.mount(
        "/care-webapp",
        StaticFiles(directory=CARE_WEBAPP_DIR, html=True),
        name="care-webapp",
    )
if os.path.isdir(ASSETS_DIR):
    app.mount(
        "/assets",
        StaticFiles(directory=ASSETS_DIR, html=False),
        name="assets",
    )

@app.get("/health")
async def health():
    return {"ok": True}

# -----------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# -----------------------------------------------------------------------------
def normalize_sheet_and_package(raw_sheet_name: str, raw_package_name: str):
    """Очищает названия от лишних символов перед записью."""
    s_name = unquote_plus(raw_sheet_name).strip()
    p_name = unquote_plus(raw_package_name).strip()
    if "[" in p_name and "]" in p_name:
        p_name = p_name.split("[")[0].strip()
    return s_name, p_name


def check_passport_expiry(passport_expiry: str) -> Optional[str]:
    """
    Проверяет срок действия паспорта.
    Если паспорт истекает в течение 6 месяцев - возвращает предупреждение.
    Возвращает None если все в порядке.

    Поддерживаемые форматы дат:
    - DD.MM.YYYY
    - YYYY-MM-DD
    - DD/MM/YYYY
    """
    if not passport_expiry or passport_expiry.strip() in ("-", ""):
        return None

    try:
        # Пробуем разные форматы
        expiry_date = None
        for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]:
            try:
                expiry_date = datetime.strptime(passport_expiry.strip(), fmt)
                break
            except ValueError:
                continue

        if not expiry_date:
            print(f"⚠️ Не удалось распознать дату паспорта: {passport_expiry}")
            return None

        # Проверяем срок действия
        now = datetime.now()
        six_months_later = now + timedelta(days=180)  # примерно 6 месяцев

        if expiry_date <= now:
            days_expired = (now - expiry_date).days
            return f"⚠️ ПАСПОРТ ПРОСРОЧЕН на {days_expired} дн."
        elif expiry_date <= six_months_later:
            days_left = (expiry_date - now).days
            months_left = days_left // 30
            return f"⚠️ Истекает через {months_left} мес. ({days_left} дн.)"

        return None  # Всё в порядке

    except Exception as e:
        print(f"❌ Ошибка проверки срока паспорта: {e}")
        return None


def get_active_tables_for_care() -> Dict[str, str]:
    """
    Возвращает словарь таблиц за текущий и следующий год.
    Если фильтр ничего не вернул, отдаём все доступные таблицы.
    """
    tables = get_accessible_tables() or {}
    now = datetime.now()
    years = {str(now.year), str(now.year + 1)}
    filtered = {name: table_id for name, table_id in tables.items() if any(y in name for y in years)}
    return filtered or tables

async def resolve_passport_path(booking) -> Optional[str]:
    """
    Возвращает путь к паспорту для брони, с фолбэком на последнее фото по ФИО.
    """
    passport_path = booking.passport_image_path
    if not passport_path and booking.guest_last_name and booking.guest_first_name:
        passport_path = await get_latest_passport_for_person(
            booking.guest_last_name,
            booking.guest_first_name
        )
    return passport_path

def make_abs_passport_path(path: Optional[str]) -> Optional[str]:
    """
    DEPRECATED: Use resolve_passport_file_path() from passport_storage.py instead.

    Приводит путь к паспорту к абсолютному:
    - если уже абсолютный – возвращаем как есть;
    - если относительный – добавляем ABS_UPLOADS_DIR.

    NOTE: This function does NOT check if the file exists.
    resolve_passport_file_path() is preferred as it:
    - Checks file existence
    - Tries multiple resolution strategies
    - Returns None if file not found
    """
    if not path:
        return None
    if os.path.isabs(path):
        return path
    return os.path.join(ABS_UPLOADS_DIR, path)

# -----------------------------------------------------------------------------
# МОДЕЛИ ДАННЫХ (Pydantic)
# -----------------------------------------------------------------------------

class PilgrimData(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    passport_num: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    passport_expiry: Optional[str] = None
    iin: Optional[str] = None
    passport_image_path: Optional[str] = None
    document_type: Optional[str] = "passport"  # "passport" или "id_card"
    is_infant: bool = False  # Флаг INF (младенец до 2 лет)
    is_child: bool = False   # Флаг CHD (ребенок)

class BookingSubmitIn(BaseModel):
    pilgrims: List[PilgrimData] = []

    package_name: str
    sheet_name: str
    table_id: str

    departure_city: str = "-"
    room_type: str = "-"
    meal_type: str = "-"
    visa_status: str = "UMRAH VISA"
    avia: str = "-"
    price: str = "0"
    amount_paid: str = "0"
    contract_number: str = "-"
    exchange_rate: str = "495"
    discount: str = "-"
    source: str = "-"
    region: str = "-"
    train: str = "-"
    manager_name_text: str = "-"
    comment: str = "-"

    placement_type: str = "separate"
    specific_row: Optional[int] = None
    manager_id: Optional[int] = None


class RescheduleRequestIn(BookingSubmitIn):
    old_booking_id: int
    old_booking_ids: List[int] = []


class CancelRequestIn(BaseModel):
    booking_id: int
    comment: str
    initiator_id: Optional[int] = None


class BookingUpdateIn(BaseModel):
    pilgrims: List[PilgrimData] = []
    # Пакет/дата не редактируем через PATCH, но можем передать для валидации
    package_name: Optional[str] = None
    sheet_name: Optional[str] = None
    table_id: Optional[str] = None
    sheet_row_number: Optional[int] = None
    verify_name: Optional[bool] = False
    departure_city: Optional[str] = None
    room_type: Optional[str] = None
    meal_type: Optional[str] = None
    visa_status: Optional[str] = None
    avia: Optional[str] = None
    price: Optional[str] = None
    amount_paid: Optional[str] = None
    contract_number: Optional[str] = None
    exchange_rate: Optional[str] = None
    discount: Optional[str] = None
    source: Optional[str] = None
    region: Optional[str] = None
    train: Optional[str] = None
    manager_name_text: Optional[str] = None
    comment: Optional[str] = None
    specific_row: Optional[int] = None

# -----------------------------------------------------------------------------
# API ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/packages")
async def api_packages(date: str, force: bool = False):
    """Поиск пакетов по дате (Smart Search)."""
    try:
        print(f"🔍 Запрос пакетов для даты: '{date}' (force={force})")

        # Правильный вызов асинхронной функции
        results = await get_packages_by_date(date_part=date, force=force)

        print(f"✅ Результат поиска: found={results.get('found')}, data_count={len(results.get('data', []))}")

        return {
            "ok": True,
            "found": results.get("found", False),
            "data": results.get("data", [])
        }
    except Exception as e:
        print(f"❌ Ошибка в /api/packages: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "found": False,
                "data": []
            }
        )

@app.post("/api/passport/parse")
async def api_passport_parse(file: UploadFile = File(...)):
    """Парсинг паспорта и извлечение данных + сохранение файла"""
    try:
        import time
        from pdf2image import convert_from_path
        from PIL import Image

        # Создаем директорию для uploads если её нет
        uploads_dir = os.path.join(PROJECT_ROOT, "tmp", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = int(time.time() * 1000)
        ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        temp_path = f"/tmp/passport_{timestamp}_temp{ext}"

        # Сохраняем временный файл
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"📥 Веб-форма: файл загружен {temp_path}")

        # Конвертируем в PNG
        png_path = os.path.join(uploads_dir, f"web_{timestamp}.png")

        try:
            if temp_path.lower().endswith('.pdf'):
                # Конвертируем PDF в PNG
                print(f"🔄 Конвертация PDF в PNG...")
                poppler_path = os.getenv("POPPLER_PATH", "/opt/homebrew/bin")
                pages = convert_from_path(temp_path, dpi=500, poppler_path=poppler_path)
                if pages:
                    pages[0].save(png_path, 'PNG')
                    print(f"✅ PDF сконвертирован: {png_path}")
            else:
                # Конвертируем изображение в PNG
                img = Image.open(temp_path)
                img.save(png_path, 'PNG')
                print(f"✅ Изображение сохранено: {png_path}")
        except Exception as conv_err:
            print(f"⚠️ Ошибка конвертации: {conv_err}, используем оригинал")
            png_path = temp_path

        # Парсим паспорт
        passport_data = await run_in_threadpool(passport_parser.parse, temp_path)

        # Удаляем временный файл (если это не финальный файл)
        if temp_path != png_path and os.path.exists(temp_path):
            os.remove(temp_path)

        if not passport_data.is_valid:
            # Удаляем сохраненный файл если данные невалидны
            if os.path.exists(png_path):
                os.remove(png_path)
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Не удалось распознать данные паспорта"}
            )

        result_data = passport_data.to_dict()
        result_data['passport_image_path'] = png_path

        print(f"✅ Веб-форма: паспорт сохранен в {png_path}")

        return {
            "ok": True,
            "data": result_data
        }

    except Exception as e:
        print(f"❌ Ошибка парсинга паспорта через веб-форму: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"Ошибка обработки файла: {str(e)}"}
        )


@app.post("/api/bookings/submit")
async def api_bookings_submit(payload: BookingSubmitIn):
    """
    Создание бронирования.
    """

    # 🔥 ДОБАВЛЕНО: Логирование входящих данных
    print("\n" + "="*60)
    print("📥 ПОЛУЧЕН ЗАПРОС /api/bookings/submit")
    print("="*60)
    print(f"Количество паломников: {len(payload.pilgrims)}")

    for i, p in enumerate(payload.pilgrims):
        print(f"\n👤 Паломник {i+1}:")
        print(f"  Фамилия: {p.last_name}")
        print(f"  Имя: {p.first_name}")
        print(f"  Пол: {p.gender}")
        print(f"  Дата рождения: {p.date_of_birth}")
        print(f"  Номер паспорта: {p.passport_num}")
        print(f"  Срок действия: {p.passport_expiry}")
        print(f"  ИИН: {p.iin}")
        print(f"  Телефон: {p.phone}")
        print(f"  🔍 DEBUG: is_infant={p.is_infant}, is_child={p.is_child}")

    print("\n📦 Общие данные:")
    print(f"  Пакет: {payload.package_name}")
    print(f"  Лист: {payload.sheet_name}")
    print(f"  Таблица: {payload.table_id}")
    print(f"  Тип комнаты: {payload.room_type}")
    print("="*60 + "\n")

    # 0. Защита от пустого списка
    if not payload.pilgrims:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Список паломников пуст"}
        )

    # 1. Проверяем/создаем менеджера в БД
    manager_id = payload.manager_id or 0
    try:
        await add_user(
            manager_id,
            payload.manager_name_text or "Manager",
            username="-",
            role="manager",
            )
    except Exception:
        pass  # если уже есть — игнорируем

    # 2. Нормализация имен
    sheet_name, package_name = normalize_sheet_and_package(
        payload.sheet_name,
        payload.package_name,
    )

    # 3. Подготовка общих данных (Common Data)
    visa_status_value = (payload.visa_status or "UMRAH VISA").strip()
    if visa_status_value.upper() == "NO VISA":
        visa_status_value = "-"

    common = {
        "table_id": payload.table_id,
        "sheet_name": sheet_name,
        "package_name": package_name,
        "region": payload.region or "-",
        "departure_city": payload.departure_city or "-",
        "source": payload.source or "-",
        "amount_paid": str(payload.amount_paid or "0"),
        "exchange_rate": str(payload.exchange_rate or "495"),
        "discount": payload.discount or "-",
        "contract_number": payload.contract_number or "-",
        "visa_status": visa_status_value,
        "avia": payload.avia or "-",
        "avia_request": payload.avia or "-",
        "room_type": payload.room_type or "-",
        "meal_type": payload.meal_type or "-",
        "train": payload.train or "-",
        "price": str(payload.price or "0"),
        "comment": payload.comment or "-",
        "manager_name_text": payload.manager_name_text or "-",
        "placement_type": payload.placement_type or "separate",
    }

    # 4. Проверка пола у всех паломников
    print(f"\n🔍 ПРОВЕРКА ПОЛА всех паломников:")
    for idx, pilgrim in enumerate(payload.pilgrims):
        gen = (pilgrim.gender or "").strip().upper()
        print(f"   Паломник {idx+1}: {pilgrim.last_name} {pilgrim.first_name}")
        print(f"      gender RAW: '{pilgrim.gender}'")
        print(f"      gender NORMALIZED: '{gen}'")
        if gen not in ("M", "F"):
            error_msg = f"❌ Пол не указан или некорректен для паломника {idx+1}: {pilgrim.last_name} {pilgrim.first_name} (получено: '{pilgrim.gender}')"
            print(error_msg)
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": f"Укажите пол (M/F) для паломника: {pilgrim.last_name} {pilgrim.first_name}",
                    "pilgrim_index": idx,
                    "pilgrim_name": f"{pilgrim.last_name} {pilgrim.first_name}"
                }
            )
    print(f"✅ Все паломники имеют корректный пол")

    # 4.1 Проверка на дубликаты по ФИО в этом листе (активные брони)
    for pilgrim in payload.pilgrims:
        ln = (pilgrim.last_name or "").strip()
        fn = (pilgrim.first_name or "").strip()
        if await booking_exists(payload.table_id, sheet_name, ln, fn):
            return JSONResponse(
                status_code=409,
                content={"ok": False, "error": f"Бронь для {ln} {fn} уже существует"}
            )

    # 5. Формирование данных для Google Sheets
    group_data_for_sheets: List[Dict[str, Any]] = []
    db_records: List[Dict[str, Any]] = []  # 🔥 Храним данные для БД
    group_members: List[str] = []

    for pilgrim in payload.pilgrims:
        full_name = f"{(pilgrim.last_name or '').strip()} {(pilgrim.first_name or '').strip()}".strip()
        group_members.append(full_name or "-")

        # 🔥 Проверка типа документа
        document_type = pilgrim.document_type or "passport"
        is_id_card = (document_type == "id_card")

        # 🔥 Проверка срока действия паспорта
        passport_warning = None
        if is_id_card:
            # Если загружено удостоверение личности
            passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            print(f"🆔 {full_name}: {passport_warning}")
        else:
            # Проверяем срок действия только для паспортов
            passport_warning = check_passport_expiry(pilgrim.passport_expiry)
            if passport_warning:
                print(f"⚠️ {full_name}: {passport_warning}")

        # Данные для Sheets
        if is_id_card:
            # Для ID card записываем только: имя, фамилию, дату рождения, ИИН, пол
            # НЕ записываем номер документа ID card
            p_sheet_data = {
                "Last Name": pilgrim.last_name or "-",
                "First Name": pilgrim.first_name or "-",
                "Gender": pilgrim.gender or "M",
                "Date of Birth": pilgrim.date_of_birth or "-",
                "Document Number": "-",  # НЕ записываем номер ID card
                "Document Expiration": "-",  # НЕ записываем срок действия ID card
                "IIN": pilgrim.iin or "-",
                "client_phone": pilgrim.phone or "-",
                "phone": pilgrim.phone or "-",
                "manager_name_text": common["manager_name_text"],
                "is_infant": pilgrim.is_infant,
                "is_child": pilgrim.is_child
            }
        else:
            # Обычный паспорт - записываем ВСЕ данные, даже если есть предупреждение
            # Предупреждение сохраняется в БД отдельно, но НЕ должно блокировать размещение
            p_sheet_data = {
                "Last Name": pilgrim.last_name or "-",
                "First Name": pilgrim.first_name or "-",
                "Gender": pilgrim.gender or "M",  # ✅ ВСЕГДА записываем пол!
                "Date of Birth": pilgrim.date_of_birth or "-",
                "Document Number": pilgrim.passport_num or "-",
                "Document Expiration": pilgrim.passport_expiry or "-",
                "IIN": pilgrim.iin or "-",
                "client_phone": pilgrim.phone or "-",
                "phone": pilgrim.phone or "-",
                "manager_name_text": common["manager_name_text"],
                "is_infant": pilgrim.is_infant,
                "is_child": pilgrim.is_child
            }
        group_data_for_sheets.append(p_sheet_data)

        # Логирование данных для Sheets
        print(f"📄 Подготовка данных для Sheets ({pilgrim.last_name}):")
        print(f"   Last Name: {p_sheet_data['Last Name']}")
        print(f"   First Name: {p_sheet_data['First Name']}")
        print(f"   Gender: {p_sheet_data['Gender']}")
        print(f"   DOB: {p_sheet_data['Date of Birth']}")
        print(f"   Doc Number: {p_sheet_data['Document Number']}")
        print(f"   IIN: {p_sheet_data['IIN']}")

        # 🔥 ИЗМЕНЕНИЕ: Подготавливаем данные для БД, но НЕ записываем
        record_db = {
            "table_id": payload.table_id,
            "sheet_name": sheet_name,
            "sheet_row_number": None,  # Будет проставлено после записи в Sheets
            "package_name": package_name,
            "region": common["region"],
            "departure_city": common["departure_city"],
            "source": common["source"],
            "amount_paid": common["amount_paid"],
            "exchange_rate": common["exchange_rate"],
            "discount": common["discount"],
            "contract_number": common["contract_number"],
            "visa_status": common["visa_status"],
            "avia": common["avia"],
            "avia_request": common["avia_request"],
            "room_type": common["room_type"],
            "meal_type": common["meal_type"],
            "train": common["train"],
            "price": common["price"],
            "comment": common["comment"],
            "manager_name_text": common["manager_name_text"],
            "placement_type": common["placement_type"],
            "guest_last_name": pilgrim.last_name or "-",
            "guest_first_name": pilgrim.first_name or "-",
            "gender": pilgrim.gender or "M",
            "date_of_birth": pilgrim.date_of_birth or "-",
            "passport_num": pilgrim.passport_num or "-",
            "passport_expiry": pilgrim.passport_expiry or "-",
            "guest_iin": pilgrim.iin or "-",
            "client_phone": pilgrim.phone or "-",
            "passport_image_path": pilgrim.passport_image_path or None,
            "passport_warning": passport_warning,  # 🔥 Сохраняем предупреждение
            "status": "new",
        }
        db_records.append(record_db)

        print(f"📝 Данные для БД подготовлены для {pilgrim.last_name}")

    # Один и тот же состав группы сохраняем в каждую запись (как список - SQLAlchemy конвертирует в JSON)
    for rec in db_records:
        rec["group_members"] = group_members

    # 5. 🔥 СНАЧАЛА пишем в БД (без номеров строк)
    db_ids: List[int] = []
    try:
        for record_db in db_records:
            booking_id = await add_booking_to_db(record_db, manager_id)
            db_ids.append(booking_id)
            print(f"✅ ID записи в БД: {booking_id}")
    except Exception as e:
        print(f"❌ Ошибка записи в БД: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": f"Ошибка записи в БД: {e}",
                "saved_rows": [],
            },
        )

    # 6. 🔥 Затем пробуем записать в Google Sheets
    saved_rows = []
    try:
        print(f"\n📊 Запись в Google Sheets...")
        saved_rows = await save_group_booking(
            group_data=group_data_for_sheets,
            common_data=common,
            placement_mode=common["placement_type"],
            specific_row=payload.specific_row,
            is_share=False,
        )

        print(f"✅ Записано в Google Sheets, строки: {saved_rows}")

    except Exception as e:
        print(f"❌ Ошибка записи в Sheets: {e}")
        import traceback
        traceback.print_exc()
        # Откат БД, если Sheets упали
        await delete_bookings_by_ids(db_ids)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": f"Ошибка записи в Google Sheets: {e}",
                "saved_rows": [],
            },
        )

    # 🔥 Если в Sheets не записалось - откатываем БД
    if not saved_rows:
        print(f"⚠️ Место не найдено в Google Sheets - откатываем БД")
        await delete_bookings_by_ids(db_ids)
        return JSONResponse(
            status_code=409,
            content={
                "ok": False,
                "error": "Место не найдено (Sheets). Попробуйте другой тип номера.",
                "saved_rows": [],
            },
        )

    # 7. Проставляем номера строк в БД
    for i, booking_id in enumerate(db_ids):
        if i < len(saved_rows):
            await update_booking_row(booking_id, saved_rows[i])
        print(f"\n💾 Запись в БД ID {booking_id} привязана к строке {saved_rows[i] if i < len(saved_rows) else 'N/A'}")
        # Уведомления шлет bot-worker. API не отправляет, чтобы избежать bot=None.
        print(f"ℹ️ Бронь #{booking_id} создана. Уведомление отправит bot-worker.")

    print("\n" + "="*60)

    # Проверяем, все ли паломники сохранились в БД
    expected_count = len(payload.pilgrims)
    saved_count = len(db_ids)

    if saved_count < expected_count:
        print(f"⚠️ ЧАСТИЧНЫЙ УСПЕХ")
        print(f"   Ожидалось паломников: {expected_count}")
        print(f"   Сохранено в БД: {saved_count}")
        print(f"   ПОТЕРЯНО: {expected_count - saved_count}")
        print(f"   Строки в таблице: {saved_rows}")
        print(f"   ID записей в БД: {db_ids}")
        print("="*60 + "\n")

        return JSONResponse(
            status_code=207,  # Multi-Status
            content={
                "ok": False,
                "partial": True,
                "error": f"Не все паломники сохранились в БД! Сохранено {saved_count} из {expected_count}",
                "db_ids": db_ids,
                "saved_rows": saved_rows,
                "expected": expected_count,
                "saved": saved_count
            }
        )

    print("✅ ЗАПРОС УСПЕШНО ОБРАБОТАН")
    print(f"   Записано паломников: {saved_count}")
    print(f"   Строки в таблице: {saved_rows}")
    print(f"   ID записей в БД: {db_ids}")
    print("="*60 + "\n")

    # 8. 📱 Отправляем WebSocket уведомления о новых телефонах
    for i, record in enumerate(db_records):
        phone = record.get("client_phone", "-")
        if phone and phone != "-":
            await notify_phone_subscribers(
                phone=phone,
                booking_id=db_ids[i] if i < len(db_ids) else 0,
                guest_name=f"{record.get('guest_first_name', '')} {record.get('guest_last_name', '')}",
                package_name=record.get("package_name", "-"),
                group_size=len(db_records),
                group_members=record.get("group_members", []),
                room_type=record.get("room_type", "-"),
                manager_name=record.get("manager_name_text", "-"),
                departure_city=record.get("departure_city", "-"),
                comment=record.get("comment", "-"),
                price=record.get("price", "0"),
                visa_status=record.get("visa_status", "-"),
                avia=record.get("avia", "-"),
                gender=record.get("gender", "M")
            )

    # 9. 🔔 Отправляем уведомления админам о новых бронях
    try:
        from bull_project.bull_bot.core.websocket_manager import notify_admins_about_new_booking

        for i, record in enumerate(db_records):
            # Подготавливаем данные брони для уведомления
            booking_data = {
                'id': db_ids[i] if i < len(db_ids) else 0,
                'package_name': record.get("package_name", "-"),
                'sheet_name': record.get("sheet_name", "-"),
                'sheet_row_number': saved_rows[i] if i < len(saved_rows) else "-",
                'guest_last_name': record.get("guest_last_name", ""),
                'guest_first_name': record.get("guest_first_name", ""),
                'gender': record.get("gender", "M"),
                'client_phone': record.get("client_phone", "-"),
                'room_type': record.get("room_type", "-"),
                'meal_type': record.get("meal_type", "-"),
                'price': record.get("price", "-"),
                'amount_paid': record.get("amount_paid", "-"),
                'region': record.get("region", "-"),
                'departure_city': record.get("departure_city", "-"),
                'visa_status': record.get("visa_status", "-"),
                'avia': record.get("avia", "-"),
                'manager_name_text': record.get("manager_name_text", "-"),
                'comment': record.get("comment", ""),
                'passport_warning': record.get("passport_warning", ""),
                'created_at': datetime.now()
            }

            await notify_admins_about_new_booking(booking_data)

    except Exception as notify_error:
        # Не прерываем выполнение если уведомление не отправилось
        print(f"⚠️ Ошибка отправки уведомления админам (не критично): {notify_error}")

    # 10. 🔔 Отправляем webhook уведомление о новой брони (временно отключено)
    # try:
    #     await notify_new_booking(
    #         bookings_data=db_records,
    #         package_name=package_name,
    #         sheet_name=sheet_name,
    #         table_id=payload.table_id,
    #         db_ids=db_ids,
    #         saved_rows=saved_rows
    #     )
    # except Exception as webhook_error:
    #     # Не прерываем выполнение если webhook не отправился
    #     print(f"⚠️ Ошибка отправки webhook (не критично): {webhook_error}")

    return {"ok": True, "db_ids": db_ids, "saved_rows": saved_rows}


@app.get("/api/history/{manager_id}")
async def get_manager_history(manager_id: int):
    """
    Получение истории бронирований менеджера
    """
    try:
        print(f"\n📋 Запрос истории для менеджера {manager_id}")
        
        # Получаем последние 100 бронирований менеджера
        bookings = await get_last_n_bookings_by_manager(manager_id, limit=100, include_cancelled=True)
        
        if not bookings:
            return {
                "ok": True,
                "bookings": [],
                "message": "История пуста"
            }
        
        
        bookings_data = []
        for b in bookings:
            passport_path = await resolve_passport_path(b)
            # group_members теперь автоматически десериализуется SQLAlchemy (тип JSON)
            group_members = b.group_members if b.group_members else []
            bookings_data.append( {
                "id": b.id,
                "manager_id": b.manager_id,
                "table_id": b.table_id,
                "sheet_name": b.sheet_name,
                "sheet_row_number": b.sheet_row_number,
                "package_name": b.package_name,
                "region": b.region,
                "departure_city": b.departure_city,
                "source": b.source,
                "amount_paid": b.amount_paid,
                "exchange_rate": b.exchange_rate,
                "discount": b.discount,
                "contract_number": b.contract_number,
                "visa_status": b.visa_status,
                "avia": b.avia,
                "avia_request": b.avia_request,
                "room_type": b.room_type,
                "meal_type": b.meal_type,
                "train": b.train,
                "price": b.price,
                "comment": b.comment,
                "manager_name_text": b.manager_name_text,
                "placement_type": b.placement_type,
                "guest_last_name": b.guest_last_name,
                "guest_first_name": b.guest_first_name,
                "gender": b.gender,
                "date_of_birth": b.date_of_birth,
                "passport_num": b.passport_num,
                "passport_expiry": b.passport_expiry,
                "guest_iin": b.guest_iin,
                "client_phone": b.client_phone,
                "passport_image_path": passport_path,
                "group_members": group_members,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None
            })
        
        print(f"✅ Найдено {len(bookings_data)} бронирований")
        
        return {
            "ok": True,
            "bookings": bookings_data
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения истории: {e}")
        import traceback
        traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": str(e)}
    )


@app.post("/api/bookings/reschedule/request")
async def api_bookings_reschedule_request(payload: RescheduleRequestIn):
    """
    Создание заявки на перенос (без записи в Google Sheets).
    Создаёт новую бронь в БД со статусом pending_reschedule + ApprovalRequest(old:<id>).
    """
    try:
        if not payload.pilgrims:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Список паломников пуст"})

        old_ids = []
        if payload.old_booking_ids:
            old_ids = [int(x) for x in payload.old_booking_ids if int(x) > 0]
        if not old_ids:
            old_ids = [int(payload.old_booking_id or 0)]
        old_ids = [x for x in old_ids if x > 0]
        if not old_ids:
            return JSONResponse(status_code=400, content={"ok": False, "error": "old_booking_id is required"})

        if len(payload.pilgrims) != len(old_ids):
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Количество паломников не совпадает с количеством переносимых броней"},
            )

        old_bookings = []
        for oid in old_ids:
            b = await get_booking_by_id(oid)
            if not b:
                return JSONResponse(status_code=404, content={"ok": False, "error": f"Старая бронь не найдена: #{oid}"})
            old_bookings.append(b)

        manager_id = payload.manager_id or 0
        try:
            await add_user(
                manager_id,
                payload.manager_name_text or "Manager",
                username="-",
                role="manager",
            )
        except Exception:
            pass

        sheet_name, package_name = normalize_sheet_and_package(payload.sheet_name, payload.package_name)

        group_members = [
            f"{(p.last_name or '').strip()} {(p.first_name or '').strip()}".strip() or "-"
            for p in payload.pilgrims
        ]

        new_booking_ids = []
        for pilgrim in payload.pilgrims:
            gender = (pilgrim.gender or "").strip().upper()
            if gender not in ("M", "F"):
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "error": "Укажите пол (M/F) для переноса"},
                )

            # Предупреждение по сроку / типу документа
            passport_warning = None
            document_type = pilgrim.document_type or "passport"
            is_id_card = (document_type == "id_card")
            if is_id_card:
                passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            else:
                passport_warning = check_passport_expiry(pilgrim.passport_expiry)
                if not passport_warning and (pilgrim.passport_expiry is None or str(pilgrim.passport_expiry).strip() == "-" or str(pilgrim.passport_expiry).strip() == ""):
                    passport_warning = "⚠️ Срок действия не распознан"

            new_booking_data = {
                "table_id": payload.table_id,
                "sheet_name": sheet_name,
                "package_name": package_name,
                "region": payload.region or "-",
                "departure_city": payload.departure_city or "-",
                "source": payload.source or "-",
                "amount_paid": str(payload.amount_paid or "0"),
                "exchange_rate": str(payload.exchange_rate or "495"),
                "discount": payload.discount or "-",
                "contract_number": payload.contract_number or "-",
                "visa_status": (payload.visa_status or "-").strip(),
                "avia": payload.avia or "-",
                "avia_request": payload.avia or "-",
                "room_type": payload.room_type or "-",
                "meal_type": payload.meal_type or "-",
                "train": payload.train or "-",
                "price": str(payload.price or "0"),
                "comment": payload.comment or "-",
                "client_phone": pilgrim.phone or "-",
                "manager_name_text": payload.manager_name_text or "-",
                "placement_type": payload.placement_type or "separate",
                "guest_last_name": (pilgrim.last_name or "-").strip().upper(),
                "guest_first_name": (pilgrim.first_name or "-").strip().upper(),
                "gender": gender,
                "date_of_birth": pilgrim.date_of_birth or "-",
                "passport_num": (pilgrim.passport_num or "-").strip().upper(),
                "passport_expiry": pilgrim.passport_expiry or "-",
                "guest_iin": pilgrim.iin or "-",
                "passport_image_path": pilgrim.passport_image_path,
                "passport_warning": passport_warning,
                "status": "pending_reschedule",
                "sheet_row_number": None,
                "group_members": group_members,
            }

            new_booking_ids.append(await add_booking_to_db(new_booking_data, manager_id))

        # Один ApprovalRequest на всю группу (ссылается на первую новую бронь)
        request_payload = {
            "old_booking_ids": old_ids,
            "new_booking_ids": new_booking_ids,
            "comment": (payload.comment or "").strip() or None,
        }
        req_id = await create_approval_request(
            new_booking_ids[0],
            "reschedule",
            manager_id,
            comment=json.dumps(request_payload, ensure_ascii=False),
        )
        for old_id in old_ids:
            await update_booking_fields(old_id, {"status": "pending_reschedule"})

        # Отправляем уведомления админам о новой заявке на перенос (через websocket_manager)
        new_booking = await get_booking_by_id(new_booking_ids[0])
        if new_booking:
            booking_dict = {
                "id": new_booking.id,
                "package_name": new_booking.package_name,
                "sheet_name": new_booking.sheet_name,
                "sheet_row_number": new_booking.sheet_row_number,
                "guest_last_name": new_booking.guest_last_name,
                "guest_first_name": new_booking.guest_first_name,
                "client_phone": new_booking.client_phone,
                "manager_name_text": new_booking.manager_name_text,
                "room_type": new_booking.room_type,
                "meal_type": new_booking.meal_type,
                "price": new_booking.price,
                "amount_paid": new_booking.amount_paid,
                "region": new_booking.region,
                "departure_city": new_booking.departure_city,
                "visa_status": new_booking.visa_status,
                "avia": new_booking.avia,
                "passport_warning": new_booking.passport_warning,
                "old_booking_ids": old_ids,
                "group_members": group_members,
            }
            await notify_admins_about_request(
                request_id=req_id,
                booking_id=new_booking.id,
                request_type="reschedule",
                booking_data=booking_dict,
                initiator_id=manager_id,
                comment=(payload.comment or "").strip() or f"Старые брони: {', '.join([str(x) for x in old_ids])}"
            )

        return {"ok": True, "booking_ids": new_booking_ids, "request_id": req_id}
    except Exception as e:
        print(f"❌ Ошибка /api/bookings/reschedule/request: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post("/api/bookings/cancel/request")
async def api_bookings_cancel_request(payload: CancelRequestIn):
    """
    Создание заявки на отмену (без прямой отмены).
    """
    try:
        booking_id = int(payload.booking_id or 0)
        comment = (payload.comment or "").strip()
        initiator_id = int(payload.initiator_id or 0)

        if booking_id <= 0:
            return JSONResponse(status_code=400, content={"ok": False, "error": "booking_id is required"})
        if not comment:
            return JSONResponse(status_code=400, content={"ok": False, "error": "comment is required"})

        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(status_code=404, content={"ok": False, "error": "booking not found"})

        req_id = await create_approval_request(booking.id, "cancel", initiator_id, comment=comment)
        await update_booking_fields(booking.id, {"status": "pending_cancel"})

        booking_dict = {
            "id": booking.id,
            "package_name": booking.package_name,
            "sheet_name": booking.sheet_name,
            "sheet_row_number": booking.sheet_row_number,
            "guest_last_name": booking.guest_last_name,
            "guest_first_name": booking.guest_first_name,
            "client_phone": booking.client_phone,
            "manager_name_text": booking.manager_name_text,
            "room_type": booking.room_type,
            "meal_type": booking.meal_type,
            "price": booking.price,
            "amount_paid": booking.amount_paid,
            "region": booking.region,
            "departure_city": booking.departure_city,
            "visa_status": booking.visa_status,
            "avia": booking.avia,
            "passport_warning": booking.passport_warning,
        }

        await notify_admins_about_request(
            request_id=req_id,
            booking_id=booking.id,
            request_type="cancel",
            booking_data=booking_dict,
            initiator_id=initiator_id,
            comment=comment,
        )

        return {"ok": True, "booking_id": booking.id, "request_id": req_id}
    except Exception as e:
        print(f"❌ Ошибка /api/bookings/cancel/request: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.post("/api/passports/upload")
async def api_passport_upload(file: UploadFile = File(...)):
    """
    Принимает файл паспорта от бота/веб-интерфейса, сохраняет, парсит и возвращает распознанные данные.
    """
    try:
        print(f"📥 Получен файл для загрузки: {file.filename}, тип: {file.content_type}")

        # Создаем директорию если не существует
        os.makedirs(ABS_UPLOADS_DIR, exist_ok=True)

        # Генерируем уникальное имя
        ts = int(datetime.now().timestamp() * 1000)
        orig_ext = os.path.splitext(file.filename or "")[1] or ".png"
        safe_ext = orig_ext if len(orig_ext) <= 5 else ".png"
        filename = f"bot_upload_{ts}{safe_ext}"
        target_path = os.path.join(ABS_UPLOADS_DIR, filename)

        print(f"💾 Сохранение файла: {target_path}")

        # Сохраняем файл
        try:
            with open(target_path, "wb") as f:
                content = await file.read()
                f.write(content)

            file_size = os.path.getsize(target_path)
            print(f"✅ Файл сохранен: {file_size / 1024:.2f} KB")
        except Exception as e:
            print(f"❌ Ошибка сохранения файла: {e}")
            raise Exception(f"Не удалось сохранить файл: {str(e)}")

        # Парсим паспорт с таймаутом
        passport_data = None
        try:
            print(f"🔍 Запуск распознавания паспорта...")

            # Используем run_in_threadpool для избежания блокировки
            from bull_project.bull_bot.core.parsers.passport_parser import PassportParser

            def parse_passport():
                try:
                    parser = PassportParser(debug=True)
                    return parser.parse(target_path)
                except Exception as e:
                    print(f"⚠️ Ошибка парсера: {e}")
                    return None

            # Запускаем парсинг в отдельном потоке с таймаутом 45 секунд
            import asyncio
            passport_data = await asyncio.wait_for(
                run_in_threadpool(parse_passport),
                timeout=45.0
            )

            if passport_data:
                print(f"✅ Паспорт распознан:")
                print(f"   Имя: {passport_data.first_name}")
                print(f"   Фамилия: {passport_data.last_name}")
                print(f"   Пол: {passport_data.gender}")
                print(f"   Дата рождения: {passport_data.dob}")
                print(f"   Номер документа: {passport_data.document_number}")
                print(f"   Срок действия: {passport_data.expiration_date}")
                print(f"   ИИН: {passport_data.iin}")
            else:
                print(f"⚠️ Паспорт не распознан, вернем только путь к файлу")

        except asyncio.TimeoutError:
            print(f"⏱️ Таймаут распознавания паспорта (>45 сек)")
            passport_data = None
        except Exception as e:
            print(f"⚠️ Ошибка распознавания паспорта: {e}")
            import traceback
            traceback.print_exc()
            passport_data = None

        # Формируем ответ
        parsed_data = {}
        passport_warning = None
        if passport_data:
            parsed_data = {
                "first_name": passport_data.first_name or "",
                "last_name": passport_data.last_name or "",
                "gender": passport_data.gender or "",
                "date_of_birth": passport_data.dob or "",
                "passport_num": passport_data.document_number or "",
                "passport_expiry": passport_data.expiration_date or "",
                "iin": passport_data.iin or "",
                "document_type": passport_data.document_type or "passport"
            }

            # 🔥 Предупреждение по паспорту — чтобы WebApp показывал сразу
            document_type = parsed_data.get("document_type") or "passport"
            expiry = (parsed_data.get("passport_expiry") or "").strip()
            if document_type == "id_card":
                passport_warning = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
            elif not expiry or expiry == "-":
                passport_warning = "⚠️ Срок действия не распознан"
            else:
                passport_warning = check_passport_expiry(expiry)

            parsed_data["passport_warning"] = passport_warning

        # ВАЖНО: Возвращаем относительный путь (только имя файла)
        # Это позволяет использовать его в разных окружениях
        return {
            "ok": True,
            "path": filename,  # Возвращаем только имя файла, не полный путь
            "absolute_path": target_path,  # Для отладки
            "parsed_data": parsed_data,    # основной ключ
            "data": parsed_data,           # алиас для фронтов, ожидающих data
            "passport_warning": passport_warning,  # алиас на верхнем уровне для удобства
            "parsed": passport_data is not None
        }

    except Exception as e:
        print(f"❌ Критическая ошибка загрузки паспорта: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.patch("/api/bookings/{booking_id}")
async def update_booking_endpoint(booking_id: int, payload: BookingUpdateIn):
    """
    Обновление существующей брони (редактирование)
    """
    try:
        print(f"\n✏️ Запрос на обновление брони #{booking_id}")

        # Получаем текущую бронь
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Бронь не найдена"}
            )

        # Формируем обновленные данные
        update_fields = {}

        p = None  # будем использовать позже при валидации
        # Обновляем данные паломника если переданы
        if payload.pilgrims and len(payload.pilgrims) > 0:
            p = payload.pilgrims[0]  # Берем первого паломника
            # Проверяем что значение не None и не пустое перед обновлением
            if p.last_name and p.last_name != "-":
                update_fields['guest_last_name'] = p.last_name
            if p.first_name and p.first_name != "-":
                update_fields['guest_first_name'] = p.first_name
            if p.gender and p.gender != "-":
                update_fields['gender'] = p.gender
            if p.date_of_birth and p.date_of_birth != "-":
                update_fields['date_of_birth'] = p.date_of_birth
            if p.passport_num and p.passport_num != "-":
                update_fields['passport_num'] = p.passport_num
            if p.passport_expiry and p.passport_expiry != "-":
                update_fields['passport_expiry'] = p.passport_expiry
                # 🔥 Проверяем срок действия паспорта при обновлении (только для паспортов, не для ID card)
                document_type = p.document_type or "passport"
                is_id_card = (document_type == "id_card")
                if not is_id_card:
                    passport_warning = check_passport_expiry(p.passport_expiry)
                    update_fields['passport_warning'] = passport_warning
                    if passport_warning:
                        print(f"⚠️ Обновление брони #{booking_id}: {passport_warning}")
            if p.iin and p.iin != "-":
                update_fields['guest_iin'] = p.iin
            if p.phone and p.phone != "-":
                update_fields['client_phone'] = p.phone

            # Обновляем фото паспорта если передано
            # Важно: пишем через update_fields, чтобы:
            # 1) запись точно попала в один commit update_booking_fields()
            # 2) в логах/ответе было видно, что обновлялось
            if p.passport_image_path:
                update_fields["passport_image_path"] = p.passport_image_path

                # 🔥 Проверяем тип документа
                document_type = p.document_type or "passport"
                is_id_card = (document_type == "id_card")

                if is_id_card:
                    # Если загружено удостоверение личности
                    update_fields['passport_warning'] = "⚠️ Загружено удостоверение личности, требуется заграничный паспорт"
                    print(f"🆔 При загрузке паспорта обнаружено удостоверение личности для брони #{booking_id}")
                else:
                    # 🔥 Проверяем существующий срок действия паспорта в БД
                    if booking.passport_expiry and booking.passport_expiry != "-":
                        passport_warning = check_passport_expiry(booking.passport_expiry)
                        update_fields['passport_warning'] = passport_warning
                        if passport_warning:
                            print(f"⚠️ При загрузке паспорта обнаружено: {passport_warning}")

        # Обновляем общие поля (пакет/дата/таблица не меняем PATCH'ем)
        if payload.departure_city: update_fields['departure_city'] = payload.departure_city
        if payload.room_type: update_fields['room_type'] = payload.room_type
        if payload.meal_type: update_fields['meal_type'] = payload.meal_type
        if payload.visa_status: update_fields['visa_status'] = payload.visa_status
        if payload.avia: update_fields['avia'] = payload.avia
        if payload.price: update_fields['price'] = payload.price
        if payload.amount_paid: update_fields['amount_paid'] = payload.amount_paid
        if payload.contract_number: update_fields['contract_number'] = payload.contract_number
        if payload.exchange_rate: update_fields['exchange_rate'] = payload.exchange_rate
        if payload.discount: update_fields['discount'] = payload.discount
        if payload.source: update_fields['source'] = payload.source
        if payload.region: update_fields['region'] = payload.region
        if payload.train: update_fields['train'] = payload.train
        if payload.manager_name_text: update_fields['manager_name_text'] = payload.manager_name_text
        if payload.comment: update_fields['comment'] = payload.comment

        # Обновляем в БД
        await update_booking_fields(booking_id, update_fields)

        print(f"✅ Бронь #{booking_id} успешно обновлена в БД")
        print(f"   Обновлено полей: {len(update_fields)}")

        # 🔥 По требованию: при обновлении/загрузке паспорта Google Sheets не трогаем вообще
        return JSONResponse(status_code=200, content={
            "ok": True,
            "booking_id": booking_id,
            "updated_fields": len(update_fields),
            "sheets_updated": False,
            "db_updated": True,
            "message": "Бронь обновлена (без изменений в Google Sheets)"
        })

    except Exception as e:
        print(f"❌ Ошибка обновления брони: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.post("/api/bookings/{booking_id}/cancel")
async def cancel_booking_endpoint(booking_id: int):
    """
    УСТАРЕЛО: прямая отмена выключена. Отмена теперь только через заявку + одобрение админа.
    """
    try:
        return JSONResponse(
            status_code=403,
            content={
                "ok": False,
                "error": "Прямая отмена отключена. Создайте заявку на отмену и дождитесь одобрения администратора.",
            },
        )
        
    except Exception as e:
        print(f"❌ Ошибка отмены брони: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/bookings/{booking_id}")
async def get_booking_details(booking_id: int):
    """
    Получение детальной информации о бронировании
    """
    try:
        booking = await get_booking_by_id(booking_id)
        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Бронь не найдена"}
            )

        return {
            "ok": True,
            "booking": {
                "id": booking.id,
                "guest_last_name": booking.guest_last_name,
                "guest_first_name": booking.guest_first_name,
                "gender": booking.gender,
                "date_of_birth": booking.date_of_birth,
                "passport_num": booking.passport_num,
                "passport_expiry": booking.passport_expiry,
                "guest_iin": booking.guest_iin,
                "client_phone": booking.client_phone,
                "package_name": booking.package_name,
                "sheet_name": booking.sheet_name,
                "table_id": booking.table_id,
                "sheet_row_number": booking.sheet_row_number,
                "departure_city": booking.departure_city,
                "room_type": booking.room_type,
                "meal_type": booking.meal_type,
                "price": booking.price,
                "amount_paid": booking.amount_paid,
                "exchange_rate": booking.exchange_rate,
                "discount": booking.discount,
                "contract_number": booking.contract_number,
                "visa_status": booking.visa_status,
                "avia": booking.avia,
                "train": booking.train,
                "region": booking.region,
                "source": booking.source,
                "manager_name_text": booking.manager_name_text,
                "comment": booking.comment,
                "passport_image_path": booking.passport_image_path,
                "status": booking.status,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


# === НОВЫЕ ENDPOINTS ДЛЯ АДМИН WEBAPP ===

@app.get("/api/admin/analytics")
async def get_admin_analytics(
    start_date: str = Query(..., description="Дата начала (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Дата конца (YYYY-MM-DD)")
):
    """
    Получение полной аналитики за период для админ панели
    """
    try:
        from datetime import datetime

        # Парсим даты
        d1 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(end_date, "%Y-%m-%d").date()

        print(f"\n📊 Запрос аналитики за период: {d1} - {d2}")

        # Получаем полную статистику
        stats = await get_full_analytics(d1, d2)

        print(f"✅ Статистика получена: {stats['total_bookings']} броней")

        return {
            "ok": True,
            **stats
        }

    except Exception as e:
        print(f"❌ Ошибка получения аналитики: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/admin/managers")
async def get_all_managers():
    """
    Получение списка всех менеджеров
    """
    try:
        managers = await get_all_managers_list()

        managers_data = []
        for m in managers:
            managers_data.append({
                "telegram_id": m.telegram_id,
                "full_name": m.full_name,
                "username": m.username,
                "role": m.role
            })

        return {
            "ok": True,
            "managers": managers_data
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/admin/manager/{manager_id}")
async def get_manager_stats(
    manager_id: int,
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    """
    Детальная статистика по конкретному менеджеру
    """
    try:
        from datetime import datetime

        # Формат даты должен быть YYYY-MM-DD (без пробелов)
        d1 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(end_date, "%Y-%m-%d").date()

        stats = await get_manager_detailed_stats(manager_id, d1, d2)

        # Преобразуем брони в JSON формат
        bookings_data = []
        for b in stats['bookings']:
            passport_path = await resolve_passport_path(b)
            bookings_data.append({
                "id": b.id,
                "guest_last_name": b.guest_last_name,
                "guest_first_name": b.guest_first_name,
                "package_name": b.package_name,
                "sheet_name": b.sheet_name,
                "price": b.price,
                "status": b.status,
                "passport_image_path": passport_path,
                "created_at": b.created_at.isoformat() if b.created_at else None
            })

        return {
            "ok": True,
            "total": stats['total'],
            "active": stats['active'],
            "cancelled": stats['cancelled'],
            "top_packages": stats['top_packages'],
            "bookings": bookings_data
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/admin/search/packages")
async def search_packages_endpoint(date: str = Query(..., description="Дата для поиска (ДД.ММ)")):
    """
    Поиск пакетов по дате
    """
    try:
        results = await search_packages_by_date(date)

        packages_data = []
        for sheet, pkg, cnt in results:
            packages_data.append({
                "sheet_name": sheet,
                "package_name": pkg,
                "count": cnt
            })

        return {
            "ok": True,
            "packages": packages_data
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/admin/bookings")
async def get_all_bookings(
    start_date: str = Query(..., description="Дата начала (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Дата конца (YYYY-MM-DD)")
):
    """
    Получение списка всех броней за период
    """
    try:
        from datetime import datetime

        d1 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(end_date, "%Y-%m-%d").date()

        bookings = await get_all_bookings_for_period(d1, d2)

        bookings_data = []
        for b in bookings:
            passport_path = await resolve_passport_path(b)
            group_members = []
            if b.group_members:
                try:
                    group_members = json.loads(b.group_members)
                except Exception:
                    group_members = []
            bookings_data.append({
                "id": b.id,
                "table_id": b.table_id,
                "guest_last_name": b.guest_last_name,
                "guest_first_name": b.guest_first_name,
                "gender": b.gender,
                "date_of_birth": b.date_of_birth,
                "guest_iin": b.guest_iin,
                "passport_num": b.passport_num,
                "passport_expiry": b.passport_expiry,
                "passport_image_path": passport_path,
                "client_phone": b.client_phone,
                "package_name": b.package_name,
                "sheet_name": b.sheet_name,
                "sheet_row_number": b.sheet_row_number,
                "room_type": b.room_type,
                "placement_type": b.placement_type,
                "meal_type": b.meal_type,
                "visa_status": b.visa_status,
                "avia": b.avia,
                "train": b.train,
                "departure_city": b.departure_city,
                "region": b.region,
                "source": b.source,
                "price": b.price,
                "amount_paid": b.amount_paid,
                "status": b.status,
                "manager_name": b.manager_name_text or b.manager_name,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "comment": b.comment or "",
                "group_members": group_members
            })

        return {
            "ok": True,
            "bookings": bookings_data
        }

    except Exception as e:
        print(f"❌ Ошибка получения броней: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


# -----------------------------------------------------------------------------
# ADMIN REQUESTS (pending cancel/reschedule)
# -----------------------------------------------------------------------------
# Вынесено в `bull_project/bull_bot/api/routes/admin_requests.py`

# -----------------------------------------------------------------------------
# CARE DEPARTMENT ENDPOINTS (Отдел Заботы)
# -----------------------------------------------------------------------------

@app.get("/api/care/tables")
async def get_care_tables():
    """Возвращает список таблиц (Google Sheets) для отдела заботы."""
    try:
        tables = get_active_tables_for_care()
        if not tables:
            return {"ok": False, "error": "Нет доступных таблиц"}

        return {"ok": True, "tables": tables}
    except Exception as e:
        print(f"❌ Ошибка получения таблиц отдела заботы: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/sheets")
async def get_care_sheets(table_id: str = Query(...)):
    """Возвращает список листов в выбранной таблице."""
    try:
        sheets = get_sheet_names(table_id) or []
        return {"ok": True, "sheets": sheets}
    except Exception as e:
        print(f"❌ Ошибка получения листов: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/search")
async def care_search_tourist(query: str = Query(..., min_length=1)):
    """
    Поиск паломника по имени/фамилии (без учета регистра, пробелов).
    Возвращает список найденных паломников с фото паспорта и всей информацией.
    """
    try:
        # Нормализуем запрос: убираем лишние пробелы
        query_normalized = " ".join(query.strip().split())

        print(f"🔍 Care Search: ищем '{query_normalized}'")

        # Поиск в БД
        results = await search_tourist_by_name(query_normalized)

        if not results:
            return {
                "ok": True,
                "results": []
            }

        # Формируем ответ
        tourists_data = []
        for booking in results:
            has_passport = bool(booking.passport_image_path)

            # Если паспорта нет, пробуем взять самый свежий по этому же ФИО
            fallback_passport = None
            if not has_passport and booking.guest_last_name and booking.guest_first_name:
                try:
                    fallback_passport = await get_latest_passport_for_person(
                        booking.guest_last_name,
                        booking.guest_first_name
                    )
                    if fallback_passport and not os.path.exists(fallback_passport):
                        fallback_passport = None
                except Exception:
                    fallback_passport = None

            tourists_data.append({
                "id": booking.id,
                "last_name": booking.guest_last_name or "-",
                "first_name": booking.guest_first_name or "-",
                "gender": booking.gender or "-",
                "date_of_birth": booking.date_of_birth or "-",
                "passport_num": booking.passport_num or "-",
                "passport_expiry": booking.passport_expiry or "-",
                "iin": booking.guest_iin or "-",
                "phone": booking.client_phone or "-",
                "package_name": booking.package_name or "-",
                "sheet_name": booking.sheet_name or "-",
                "placement_type": booking.placement_type or "-",
                "room_type": booking.room_type or "-",
                "meal_type": booking.meal_type or "-",
                "price": booking.price or "-",
                "amount_paid": booking.amount_paid or "-",
                "manager_name": booking.manager_name_text or "-",
                "comment": booking.comment or "",
                "visa_status": booking.visa_status or "-",
                "avia": booking.avia or "-",
                "train": booking.train or "-",
                "region": booking.region or "-",
                "departure_city": booking.departure_city or "-",
                "source": booking.source or "-",
                "passport_image_path": booking.passport_image_path or fallback_passport or None,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "status": booking.status
            })
            print(
                f"  Паломник {booking.guest_last_name} {booking.guest_first_name}: "
                f"паспорт={has_passport}, путь={booking.passport_image_path or fallback_passport}"
            )

        print(f"✅ Найдено {len(tourists_data)} результатов")

        return {
            "ok": True,
            "results": tourists_data
        }

    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/passport-photo/{booking_id}")
async def get_passport_photo(booking_id: int):
    """
    Возвращает фото паспорта для конкретной брони.
    """
    try:
        booking = await get_booking_by_id(booking_id)

        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Booking not found"}
            )

        # Ищем актуальный путь: сначала в самой брони, иначе берём самое свежее фото по ФИО
        passport_path = booking.passport_image_path
        if not passport_path and booking.guest_last_name and booking.guest_first_name:
            passport_path = await get_latest_passport_for_person(
                booking.guest_last_name,
                booking.guest_first_name
            )

        if not passport_path:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "No passport image for this booking"}
            )

        # Резолвим путь к паспорту (поддерживает и абсолютные, и относительные пути)
        resolved_path = resolve_passport_file_path(passport_path)

        # Проверяем существование файла
        if not resolved_path or not os.path.exists(resolved_path):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": f"Passport image file not found. Original path: {passport_path}, tried to resolve to: {resolved_path or 'N/A'}"}
            )

        passport_path = resolved_path

        # Определяем тип файла по расширению
        file_ext = os.path.splitext(passport_path)[1].lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf'
        }
        media_type = media_types.get(file_ext, 'image/png')  # По умолчанию PNG

        # Отдаем файл
        return FileResponse(
            passport_path,
            media_type=media_type,
            filename=f"passport_{booking_id}{file_ext}"
        )

    except Exception as e:
        print(f"❌ Ошибка получения фото паспорта: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/passport-pdf/{booking_id}")
async def get_passport_pdf(booking_id: int):
    """
    Возвращает паспорт в формате PDF с текстовым слоем (searchable PDF).
    Если оригинал - изображение, конвертирует в PDF с OCR.
    Если уже PDF - возвращает как есть.
    """
    try:
        booking = await get_booking_by_id(booking_id)

        if not booking:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Booking not found"}
            )

        # Формируем имя файла из ФИО
        import re
        last_name = (booking.guest_last_name or "").strip()
        first_name = (booking.guest_first_name or "").strip()

        # Безопасное имя файла: убираем спецсимволы
        safe_last_name = re.sub(r'[^\w\s-]', '', last_name).strip()
        safe_first_name = re.sub(r'[^\w\s-]', '', first_name).strip()

        if safe_last_name and safe_first_name:
            pdf_filename = f"{safe_last_name}_{safe_first_name}_passport.pdf"
        else:
            pdf_filename = f"passport_{booking_id}.pdf"

        # Ищем актуальный путь к паспорту
        passport_path = booking.passport_image_path
        if not passport_path and booking.guest_last_name and booking.guest_first_name:
            passport_path = await get_latest_passport_for_person(
                booking.guest_last_name,
                booking.guest_first_name
            )

        if not passport_path:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "No passport image for this booking"}
            )

        # Резолвим путь к паспорту (поддерживает и абсолютные, и относительные пути)
        resolved_path = resolve_passport_file_path(passport_path)

        # Проверяем существование файла
        if not resolved_path or not os.path.exists(resolved_path):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": f"Passport image file not found. Original path: {passport_path}, tried to resolve to: {resolved_path or 'N/A'}"}
            )

        passport_path = resolved_path

        # Если уже PDF - отдаем как есть
        if passport_path.lower().endswith('.pdf'):
            return FileResponse(
                passport_path,
                media_type='application/pdf',
                filename=pdf_filename,
                headers={
                    'Content-Disposition': f'attachment; filename="{pdf_filename}"'
                }
            )

        # Если изображение - конвертируем в PDF
        try:
            import tempfile
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            from PIL import Image
            from fastapi import Response
            import urllib.parse
            import io

            # Создаем временный PDF файл
            temp_pdf = tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False,
                dir=os.path.dirname(passport_path)
            )
            temp_pdf_path = temp_pdf.name
            temp_pdf.close()

            # Создаем PDF с изображением
            print(f"🔄 Создание PDF для паспорта {booking_id}...")

            img = Image.open(passport_path)
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            if aspect_ratio > 1:
                page_width = 842
                page_height = 842 / aspect_ratio
            else:
                page_height = 842
                page_width = 842 * aspect_ratio

            # Пишем PDF с адаптивным сжатием изображения (чтобы не было 10+ MB)
            def prepare_jpeg(max_side: int, quality: int) -> bytes:
                if img.mode != "RGB":
                    img_rgb = img.convert("RGB")
                else:
                    img_rgb = img
                w, h = img_rgb.size
                if max(w, h) > max_side:
                    scale = max_side / float(max(w, h))
                    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                    img_rgb = img_rgb.resize(new_size, Image.LANCZOS)
                buf = io.BytesIO()
                img_rgb.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
                return buf.getvalue()

            presets = [
                (2000, 85),
                (1800, 80),
                (1600, 75),
                (1400, 70),
            ]
            target_max_bytes = 1_150_000  # ~1.1MB
            last_size = None

            for (max_side, quality) in presets:
                jpeg_bytes = prepare_jpeg(max_side=max_side, quality=quality)

                c = canvas.Canvas(temp_pdf_path, pagesize=(page_width, page_height))
                c.setPageCompression(1)
                c.drawImage(ImageReader(io.BytesIO(jpeg_bytes)), 0, 0, width=page_width, height=page_height)
                c.save()

                try:
                    last_size = os.path.getsize(temp_pdf_path)
                except Exception:
                    last_size = None
                if last_size is not None and last_size <= target_max_bytes:
                    break

            result_path = temp_pdf_path

            # Проверяем что файл создан и не пустой
            if not os.path.exists(result_path):
                raise Exception(f"PDF не создан: {result_path}")

            file_size = os.path.getsize(result_path)
            if file_size == 0:
                raise Exception("PDF файл пустой")

            print(f"✅ PDF создан: {file_size} байт, путь: {result_path}")

            # Читаем файл в память для гарантированной отправки
            with open(result_path, 'rb') as f:
                pdf_content = f.read()

            print(f"✅ PDF прочитан в память: {len(pdf_content)} байт")

            # Удаляем временный файл
            try:
                os.remove(result_path)
                print(f"🗑️ Временный файл удален: {result_path}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить временный файл: {e}")

            # Кодируем имя файла по RFC 5987 для поддержки non-ASCII
            encoded_filename = urllib.parse.quote(pdf_filename)

            print(f"📤 Отправка PDF: {pdf_filename} ({encoded_filename})")

            # Возвращаем через Response с явным содержимым
            return Response(
                content=pdf_content,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{pdf_filename}"; filename*=UTF-8\'\'{encoded_filename}',
                    'Content-Length': str(len(pdf_content)),
                    'Cache-Control': 'no-cache',
                }
            )

        except Exception as pdf_error:
            print(f"❌ Ошибка создания PDF: {pdf_error}")
            import traceback
            traceback.print_exc()

            # Fallback: отдаем оригинальное изображение
            file_ext = os.path.splitext(passport_path)[1].lower()
            media_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
            }
            media_type = media_types.get(file_ext, 'image/png')

            return FileResponse(
                passport_path,
                media_type=media_type,
                filename=f"passport_{booking_id}{file_ext}"
            )

    except Exception as e:
        print(f"❌ Ошибка получения паспорта в PDF: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/packages-by-date")
async def get_packages_by_date_for_care(
    table_id: str = Query(...),
    sheet_name: str = Query(...)
):
    """
    Возвращает список пакетов на конкретной дате (для выбора date sheet).
    """
    try:
        print(f"📋 Care Packages: table_id={table_id}, sheet_name={sheet_name}")

        # Сначала пробуем прочитать актуальные пакеты напрямую из Google Sheet
        packages_map = get_packages_from_sheet(table_id, sheet_name)
        packages = list(packages_map.values()) if packages_map else []

        # Если из таблицы ничего не нашли (например, проблемы с форматами),
        # пробуем достать из БД как фолбэк.
        if not packages:
            packages = await get_db_packages_list(table_id, sheet_name)

        return {
            "ok": True,
            "packages": list(packages)
        }

    except Exception as e:
        print(f"❌ Ошибка получения пакетов: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/bookings-in-package")
async def get_bookings_in_package_for_care(
    table_id: str = Query(...),
    sheet_name: str = Query(...),
    package_name: str = Query(...)
):
    """
    Возвращает все брони в конкретном пакете со всей информацией.
    """
    try:
        print(f"📋 Care Bookings: package='{package_name}', sheet='{sheet_name}'")

        bookings = await get_all_bookings_in_package(table_id, sheet_name, package_name)

        bookings_data = []
        for b in bookings:
            passport_path = await resolve_passport_path(b)
            bookings_data.append({
                "id": b.id,
                "last_name": b.guest_last_name or "-",
                "first_name": b.guest_first_name or "-",
                "package_name": b.package_name or "-",
                "sheet_name": b.sheet_name or "-",
                "table_id": b.table_id or "-",
                "gender": b.gender or "-",
                "date_of_birth": b.date_of_birth or "-",
                "passport_num": b.passport_num or "-",
                "passport_expiry": b.passport_expiry or "-",
                "iin": b.guest_iin or "-",
                "phone": b.client_phone or "-",
                "room_type": b.room_type or "-",
                "meal_type": b.meal_type or "-",
                "price": b.price or "-",
                "amount_paid": b.amount_paid or "-",
                "manager_name": b.manager_name_text or "-",
                "comment": b.comment or "",
                "visa_status": b.visa_status or "-",
                "avia": b.avia or "-",
                "train": b.train or "-",
                "region": b.region or "-",
                "departure_city": b.departure_city or "-",
                "source": b.source or "-",
                "passport_image_path": passport_path or None,
                "sheet_row_number": b.sheet_row_number,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "status": b.status
            })

        print(f"✅ Найдено {len(bookings_data)} броней в пакете")

        return {
            "ok": True,
            "bookings": bookings_data
        }

    except Exception as e:
        print(f"❌ Ошибка получения броней: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/care/phones-by-package")
async def get_phones_by_package(
    table_id: str = Query(...),
    sheet_name: str = Query(...),
    package_name: str = Query(...)
):
    """
    Возвращает список телефонов с именами для конкретного пакета.
    """
    try:
        print(f"📞 Care Phones: package='{package_name}'")

        bookings = await get_all_bookings_in_package(table_id, sheet_name, package_name)

        phones_data = []
        for b in bookings:
            if b.client_phone and b.client_phone != "-":
                phones_data.append({
                    "name": f"{b.guest_last_name or ''} {b.guest_first_name or ''}".strip(),
                    "phone": b.client_phone
                })

        print(f"✅ Найдено {len(phones_data)} телефонов")

        return {
            "ok": True,
            "phones": phones_data
        }

    except Exception as e:
        print(f"❌ Ошибка получения телефонов: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )

# ============= ADMIN TOOLS =============

@app.get("/api/admin/download-all-passports")
async def download_all_passports():
    """
    Скачать все паспорта из volume в виде ZIP архива
    ВАЖНО: Используйте этот эндпоинт только для резервного копирования!
    """
    try:
        import zipfile
        import tempfile
        from pathlib import Path

        print(f"📦 Запрос на скачивание всех паспортов из {ABS_UPLOADS_DIR}")

        # Проверяем что директория существует
        if not os.path.exists(ABS_UPLOADS_DIR):
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": f"Директория {ABS_UPLOADS_DIR} не найдена"}
            )

        # Получаем список всех файлов
        all_files = []
        for root, dirs, files in os.walk(ABS_UPLOADS_DIR):
            for file in files:
                # Пропускаем временные файлы
                if file.endswith(('_preprocessed.jpg', '_temp.jpg', '_temp_ocr.jpg')):
                    continue
                full_path = os.path.join(root, file)
                all_files.append(full_path)

        if not all_files:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Паспортов не найдено"}
            )

        print(f"✅ Найдено {len(all_files)} файлов")

        # Создаем временный ZIP файл
        temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_zip_path = temp_zip.name
        temp_zip.close()

        # Упаковываем все файлы в ZIP
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in all_files:
                # Получаем относительный путь для архива
                arcname = os.path.relpath(file_path, ABS_UPLOADS_DIR)
                zipf.write(file_path, arcname)
                print(f"  ✅ Добавлен: {arcname}")

        zip_size = os.path.getsize(temp_zip_path)
        print(f"📦 ZIP архив создан: {zip_size / 1024 / 1024:.2f} MB")

        # Возвращаем ZIP файл
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"passports_backup_{timestamp}.zip"

        return FileResponse(
            temp_zip_path,
            media_type='application/zip',
            filename=filename,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            },
            background=None  # Не удаляем файл автоматически, удалим вручную после отправки
        )

    except Exception as e:
        print(f"❌ Ошибка создания архива: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/admin/system-check")
async def system_check():
    """
    Проверка системы: OCR, директории, память
    """
    try:
        import sys
        import psutil

        result = {
            "ok": True,
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        # Проверка 1: Директория uploads
        result["checks"]["uploads_dir"] = {
            "path": ABS_UPLOADS_DIR,
            "exists": os.path.exists(ABS_UPLOADS_DIR),
            "writable": os.access(ABS_UPLOADS_DIR, os.W_OK) if os.path.exists(ABS_UPLOADS_DIR) else False
        }

        # Проверка 2: EasyOCR
        try:
            import easyocr
            result["checks"]["easyocr"] = {
                "installed": True,
                "version": getattr(easyocr, '__version__', 'unknown')
            }

            # Пробуем загрузить модели
            try:
                reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                result["checks"]["easyocr"]["models_loaded"] = True
                result["checks"]["easyocr"]["status"] = "✅ Работает"
            except Exception as e:
                result["checks"]["easyocr"]["models_loaded"] = False
                result["checks"]["easyocr"]["error"] = str(e)
                result["checks"]["easyocr"]["status"] = f"❌ Ошибка загрузки моделей: {str(e)[:100]}"
        except ImportError:
            result["checks"]["easyocr"] = {
                "installed": False,
                "status": "❌ Не установлен"
            }

        # Проверка 3: Память
        try:
            memory = psutil.virtual_memory()
            result["checks"]["memory"] = {
                "total_mb": round(memory.total / 1024 / 1024, 2),
                "available_mb": round(memory.available / 1024 / 1024, 2),
                "used_percent": memory.percent,
                "status": "✅ OK" if memory.percent < 90 else "⚠️ Мало памяти"
            }
        except:
            result["checks"]["memory"] = {"status": "❌ Не удалось проверить"}

        # Проверка 4: Torch (для EasyOCR)
        try:
            import torch
            result["checks"]["torch"] = {
                "installed": True,
                "version": torch.__version__,
                "cuda_available": torch.cuda.is_available()
            }
        except ImportError:
            result["checks"]["torch"] = {
                "installed": False,
                "status": "❌ Не установлен (требуется для EasyOCR)"
            }

        # Проверка 5: Python
        result["checks"]["python"] = {
            "version": sys.version,
            "executable": sys.executable
        }

        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/admin/passports-stats")
async def get_passports_stats():
    """
    Получить статистику по файлам паспортов
    """
    try:
        if not os.path.exists(ABS_UPLOADS_DIR):
            return {
                "ok": True,
                "total_files": 0,
                "total_size_mb": 0,
                "directory": ABS_UPLOADS_DIR,
                "exists": False
            }

        # Подсчитываем файлы
        total_files = 0
        total_size = 0
        file_types = {}

        for root, dirs, files in os.walk(ABS_UPLOADS_DIR):
            for file in files:
                # Пропускаем временные файлы
                if file.endswith(('_preprocessed.jpg', '_temp.jpg', '_temp_ocr.jpg')):
                    continue

                full_path = os.path.join(root, file)
                file_size = os.path.getsize(full_path)

                total_files += 1
                total_size += file_size

                # Группируем по расширениям
                ext = os.path.splitext(file)[1].lower()
                if ext not in file_types:
                    file_types[ext] = {"count": 0, "size": 0}
                file_types[ext]["count"] += 1
                file_types[ext]["size"] += file_size

        return {
            "ok": True,
            "total_files": total_files,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "file_types": file_types,
            "directory": ABS_UPLOADS_DIR,
            "exists": True
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


# Корневой маршрут для WebApp
@app.get("/")
async def root():
    """Главная страница"""
    index_path = os.path.join(CARE_WEBAPP_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Bull API", "status": "running"}


# Раздача всех статических файлов
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Fallback для всех файлов"""
    
    # Игнорируем API роуты
    if full_path.startswith("api/"):
        return {"error": "API endpoint not found"}
    
    # Ищем файл в care_webapp
    file_path = os.path.join(CARE_WEBAPP_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Ищем файл в assets
    asset_path = os.path.join(ASSETS_DIR, full_path)
    if os.path.exists(asset_path) and os.path.isfile(asset_path):
        return FileResponse(asset_path)
    
    # Для всех остальных запросов возвращаем index.html (SPA fallback)
    index_path = os.path.join(CARE_WEBAPP_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"error": "Not found"}


if __name__ == "__main__":
    import uvicorn
    # Koyeb/Render/etc. прокидывают порт через env, поэтому пробуем PORT/PORT0
    port = int(os.getenv("PORT") or os.getenv("PORT0") or "8000")
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
    )
