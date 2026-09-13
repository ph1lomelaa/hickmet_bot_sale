from typing import Optional, List

from pydantic import BaseModel


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
    is_infant: bool = False  # INF
    is_child: bool = False  # CHD


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
    confirm_duplicates: bool = False


class RescheduleRequestIn(BookingSubmitIn):
    old_booking_id: int
    old_booking_ids: List[int] = []


class CancelRequestIn(BaseModel):
    booking_id: int
    comment: str
    initiator_id: Optional[int] = None


class BookingUpdateIn(BaseModel):
    pilgrims: List[PilgrimData] = []
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
    placement_type: Optional[str] = None
    specific_row: Optional[int] = None
    manager_id: Optional[int] = None
