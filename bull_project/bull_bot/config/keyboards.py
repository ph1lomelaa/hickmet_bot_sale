from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def manager_kb():
    """Меню для Менеджера (Продажи)"""
    from aiogram.types import WebAppInfo
    import time
    # Используем timestamp для cache-busting (Telegram не будет кэшировать разные URLs)
    cache_bust = int(time.time())
    HISTORY_URL = f"https://ph1lomelaa.github.io/book/history_v2.html?t={cache_bust}"
    OPEN_DATE_URL = f"https://ph1lomelaa.github.io/book/open_date.html?t={cache_bust}" 

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать бронь", callback_data="create_booking")],
        [InlineKeyboardButton(text="История бронирования", web_app=WebAppInfo(url=HISTORY_URL))],
        [InlineKeyboardButton(text="OPEN DATE", web_app=WebAppInfo(url=OPEN_DATE_URL))],
    ])

def care_kb():
    from aiogram.types import WebAppInfo
    import time
    cache_bust = int(time.time())

    CARE_BOOKINGS_URL = f"https://ph1lomelaa.github.io/book/admin-bookings.html?t={cache_bust}"
    CARE_SEARCH_URL = f"https://ph1lomelaa.github.io/book/search-pilgrim.html?t={cache_bust}"
    CARE_PACKAGES_URL = f"https://ph1lomelaa.github.io/book/package-lists.html?t={cache_bust}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Список броней", web_app=WebAppInfo(url=CARE_BOOKINGS_URL))],
        [InlineKeyboardButton(text="Найти паломника", web_app=WebAppInfo(url=CARE_SEARCH_URL))],
        [InlineKeyboardButton(text="Списки по пакетам", web_app=WebAppInfo(url=CARE_PACKAGES_URL))],
    ])

def admin_kb():
    from aiogram.types import WebAppInfo
    import time
    cache_bust = int(time.time())
    
    ADMIN_PANEL_URL = f"https://ph1lomelaa.github.io/book/admin-panel.html?t={cache_bust}"
    ADMIN_BOOKINGS_URL = f"https://ph1lomelaa.github.io/book/admin-bookings.html?t={cache_bust}"
    ADMIN_REQUESTS_URL = f"https://ph1lomelaa.github.io/book/admin-requests.html?t={cache_bust}"
    CARE_SEARCH_URL = f"https://ph1lomelaa.github.io/book/search-pilgrim.html?t={cache_bust}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Аналитика", web_app=WebAppInfo(url=ADMIN_PANEL_URL))],
        [InlineKeyboardButton(text="Список броней", web_app=WebAppInfo(url=ADMIN_BOOKINGS_URL))],
        [InlineKeyboardButton(text="Заявки на отмену/перенос", web_app=WebAppInfo(url=ADMIN_REQUESTS_URL))],
        [InlineKeyboardButton(text="Создать бронь", callback_data="create_booking")],
        [InlineKeyboardButton(text="Найти паломника", web_app=WebAppInfo(url=CARE_SEARCH_URL))],
        # У админа убираем быстрый переход "Перенос/Отмена" из меню (оставляем только уведомления/заявки через отдельные каналы)
        [InlineKeyboardButton(text="Запросы 4U", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Настройки уведомлений", callback_data="admin_notify_menu")],
    ])

from aiogram.utils.keyboard import InlineKeyboardBuilder

def search_results_kb(results):
    builder = InlineKeyboardBuilder()

    for res in results:
        pass

    return builder.as_markup()

def get_menu_by_role(role: str) -> InlineKeyboardMarkup:
    """
    Эта функция решает, какое меню показать человеку
    в зависимости от его роли в Базе Данных.
    """
    if role == "admin":
        return admin_kb()
    elif role == "care":
        return care_kb()
    else:
        return manager_kb() # По умолчанию показываем меню менеджера

# ==================== КЛАВИАТУРЫ GOOGLE SHEETS ====================

def kb_select_table(tables: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, sheet_id in tables.items():
        builder.button(text=name, callback_data=f"sel_tab:{sheet_id}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()

def kb_select_sheet(sheets: list, has_more: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sheet_name in sheets:
        builder.button(text=sheet_name, callback_data=f"sel_date:{sheet_name}")

    if has_more:
        builder.button(text="⬇️ Показать все", callback_data="show_all_dates")

    builder.button(text="🔙 Назад", callback_data="back_to_tables")
    builder.adjust(1)
    return builder.as_markup()

def kb_select_package(packages: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Кнопки пакетов
    for row_id, pkg_name in packages.items():
        builder.button(text=pkg_name, callback_data=f"sel_pkg:{row_id}")

    # Спец. кнопка
    builder.button(text="🔵 Запросить пакет 4U", callback_data="req_4u")

    builder.button(text="🔙 Назад", callback_data="back_to_dates")
    builder.adjust(1)
    return builder.as_markup()

# ==================== КЛАВИАТУРЫ АНКЕТЫ ====================

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Верно", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Переснять", callback_data="confirm_no")],
    ])

train_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=" YES", callback_data="train_yes"),
     InlineKeyboardButton(text=" NO", callback_data="train_no")]
])
def visa_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить пустым", callback_data="visa_Empty")],
    ])

def meal_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" HB ", callback_data="meal_HB")],
        [InlineKeyboardButton(text=" BB ", callback_data="meal_BB")],
        [InlineKeyboardButton(text=" RO ", callback_data="meal_RO")],
    ])

def room_kb():
    builder = InlineKeyboardBuilder()
    # Ваши варианты
    builder.button(text="Quadro", callback_data="room_QUAD")
    builder.button(text="Triple", callback_data="room_TRPL")
    builder.button(text="Double", callback_data="room_DBL")
    builder.button(text="Single", callback_data="room_SGL")
    # Доп
    builder.button(text="INF", callback_data="room_INF")
    builder.button(text="CHILD", callback_data="room_CHILD")
    builder.adjust(2)
    return builder.as_markup()

def placement_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Произвольное размещение", callback_data="place_random")],
        [InlineKeyboardButton(text=" Разместить с человеком", callback_data="place_specific")],
    ])

def comment_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")],
    ])

def preview_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_booking")],
        [InlineKeyboardButton(text="🔄 Заново", callback_data="create_booking")],
    ])

def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])

def main_menu_kb():
    # Эта функция оставлена для совместимости, если где-то еще вызывается,
    # но лучше использовать get_menu_by_role
    return manager_kb()

def yes_no_kb(text="Пропустить"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data="skip")],
    ])
def count_kb():
    """Клавиатура для выбора количества паломников"""
    builder = InlineKeyboardBuilder()
    # Кнопки 1-10
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"count_{i}")
    builder.adjust(5) # По 5 в ряд
    return builder.as_markup()

def family_or_separate_kb():
    """Выбор типа размещения для группы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍👩‍👧 ВМЕСТЕ (Семья)", callback_data="place_family")],
        [InlineKeyboardButton(text="🚻 РАЗДЕЛЬНО (М/Ж)", callback_data="place_separate")],
    ])
