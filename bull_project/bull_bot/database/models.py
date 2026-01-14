from sqlalchemy import BigInteger, String, Column, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    telegram_id = Column(BigInteger, primary_key=True)
    full_name = Column(String)
    username = Column(String, nullable=True)
    role = Column(String, default="manager")
    created_at = Column(DateTime, default=datetime.now)

class Request4U(Base):
    __tablename__ = 'requests_4u'

    id = Column(Integer, primary_key=True)
    manager_id = Column(BigInteger)
    manager_name = Column(String)

    table_id = Column(String)
    dates = Column(String)       
    pilgrim_count = Column(Integer) 
    room_type = Column(String)   

    status = Column(String, default="pending") 
    created_at = Column(DateTime, default=datetime.now)
    created_sheet_name = Column(String, nullable=True) 


class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    manager_id = Column(BigInteger, ForeignKey('users.telegram_id'))

    table_id = Column(String)
    sheet_name = Column(String)
    sheet_row_number = Column(Integer, nullable=True)

    package_name = Column(String)
    region = Column(String)          # Регион
    departure_city = Column(String)  # Город вылета
    source = Column(String)          # Источник (Инстаграм, знакомые...)
    amount_paid = Column(String)     # Сумма оплаты (предоплата)
    exchange_rate = Column(String)   # Курс доллара
    discount = Column(String)        # Скидка от кого
    avia_request = Column(String)    # Авиа запрос (можно хранить общий или детали)

    visa_status = Column(String)
    avia = Column(String)
    room_type = Column(String)
    meal_type = Column(String)
    train = Column(String)

    # --- ДАННЫЕ ПАСПОРТА ---
    guest_last_name = Column(String)
    guest_first_name = Column(String)
    gender = Column(String)
    date_of_birth = Column(String)
    passport_num = Column(String)
    passport_expiry = Column(String)
    guest_iin = Column(String)
    contract_number = Column(String, nullable=True)
    group_members = Column(JSON, nullable=True)

    # --- ОСТАЛЬНОЕ ---
    price = Column(String)
    comment = Column(Text, nullable=True)
    client_phone = Column(String)
    manager_name_text = Column(String)
    placement_type = Column(String)
    passport_image_path = Column(String, nullable=True)
    passport_warning = Column(String, nullable=True)  # Предупреждение о сроке паспорта

    status = Column(String, default="new") # new, cancelled
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AdminSettings(Base):
    __tablename__ = 'admin_settings'
    admin_id = Column(BigInteger, primary_key=True)  # telegram_id админа
    notify_new = Column(Integer, default=0)          # 0/1
    notify_cancel = Column(Integer, default=0)
    notify_reschedule = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class ApprovalRequest(Base):
    __tablename__ = 'approval_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'))
    request_type = Column(String)  # cancel | reschedule
    initiator_id = Column(BigInteger, ForeignKey('users.telegram_id'))
    status = Column(String, default="pending")  # pending | approved | rejected
    created_at = Column(DateTime, default=datetime.now)
    comment = Column(Text, nullable=True)  # для reschedule можно хранить old_booking_id


class OpenDateBooking(Base):
    """
    Хранит паломников, записанных на OPEN DATE (без конкретной даты).
    Записываются в Google Sheets таблицу "Certificate 2025" и ждут выбора даты.
    """
    __tablename__ = 'open_date_bookings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    manager_id = Column(BigInteger, ForeignKey('users.telegram_id'))
    manager_name_text = Column(String)

    # Данные группы паломников (JSON массив)
    pilgrim_data = Column(JSON)  # [{last_name, first_name, gender, dob, passport_num, passport_expiry, iin}, ...]

    # Параметры брони
    room_type = Column(String, nullable=True)  # Может быть "не указано"
    meal_type = Column(String, nullable=True)  # Может быть "не указано"
    price = Column(String, nullable=True)
    region = Column(String, nullable=True)
    departure_city = Column(String, nullable=True)

    # Контактная информация
    client_phone = Column(String)
    comment = Column(Text, nullable=True)

    # Google Sheets данные
    google_sheet_row = Column(Integer, nullable=True)  # Номер строки в Certificate 2025

    # Статус
    status = Column(String, default="OPEN")  # OPEN | CONVERTED

    # Временные метки
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
