"""
Парсер паспортов на EasyOCR (уже установлен!)
Работает лучше Tesseract, проще PaddleOCR
"""

import easyocr
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import numpy as np

# OpenCV - опциональная зависимость для продвинутого препроцессинга
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    cv2 = None

# passporteye удален (потребляет много памяти)
try:
    from passporteye import read_mrz
    HAS_PASSPORTEYE = True
except ImportError:
    HAS_PASSPORTEYE = False
    read_mrz = None
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
import os


@dataclass
class PassportData:
    """Структура данных паспорта"""
    last_name: str = ""
    first_name: str = ""
    gender: str = ""
    dob: str = ""
    iin: str = ""
    document_number: str = ""
    expiration_date: str = ""
    phone: str = ""
    nationality: str = ""
    document_type: str = ""  # "passport" или "id_card"

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()

    @property
    def is_valid(self) -> bool:
        has_name = bool(self.last_name or self.first_name)
        has_iin = len(self.iin) == 12 if self.iin else False
        has_doc = bool(self.document_number)
        return has_name and (has_iin or has_doc)

    def to_dict(self) -> dict:
        """Возвращает данные в формате для API (совместимость с booking_handlers.py)"""
        return {
            # Snake_case формат (для writer.py и test скриптов)
            "last_name": self.last_name or "-",
            "first_name": self.first_name or "-",
            "gender": self.gender or "M",
            "date_of_birth": self.dob or "-",
            "passport_num": self.document_number or "-",
            "phone": self.phone or "-",
            "nationality": self.nationality or "KAZ",
            "iin": self.iin or "-",
            "document_type": self.document_type or "passport",
            # Дополнительные поля для совместимости с booking_handlers.py
            "Last Name": self.last_name or "-",
            "First Name": self.first_name or "-",
            "Gender": self.gender or "M",
            "Date of Birth": self.dob or "-",
            "Document Number": self.document_number or "-",
            "Document Expiration": self.expiration_date or "-",
            "IIN": self.iin or "-",
            "MRZ_LAST": getattr(self, "mrz_last_name", None),
            "MRZ_FIRST": getattr(self, "mrz_first_name", None),
        }


class PassportParserEasyOCR:
    """
    Парсер на EasyOCR + PassportEye
    Лучше работает, чем Tesseract
    """

    def __init__(self, poppler_path: str = None, debug: bool = False):
        self.poppler_path = poppler_path
        self.debug = debug

        # Инициализация EasyOCR (английский + русский)
        # Первый запуск скачает модели (~100MB)
        self.reader = easyocr.Reader(['en', 'ru'])

        # Более полный маппинг кириллицы в латиницу (покоcимый OCR)
        self.cyr_to_lat_map = {
            **{ord(c): l for c, l in {
                "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D",
                "Е": "E", "Ё": "E", "Ж": "Z", "З": "Z", "И": "I", "Й": "Y",
                "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P",
                "Р": "R", "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "H",
                "Ц": "C", "Ч": "C", "Ш": "S", "Щ": "S", "Ы": "Y", "Э": "E",
                "Ю": "U", "Я": "A", "Ь": "", "Ъ": "", "І": "I", "Ї": "I",
            }.items()},
            **{ord(c.lower()): l.lower() for c, l in {
                "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D",
                "Е": "E", "Ё": "E", "Ж": "Z", "З": "Z", "И": "I", "Й": "Y",
                "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P",
                "Р": "R", "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "H",
                "Ц": "C", "Ч": "C", "Ш": "S", "Щ": "S", "Ы": "Y", "Э": "E",
                "Ю": "U", "Я": "A", "Ь": "", "Ъ": "", "І": "I", "Ї": "I",
            }.items()}
        }

    def normalize_text(self, text: str) -> str:
        """
        Переводит похожие кириллические буквы в латиницу и поднимает регистр.
        Помогает, когда OCR смешивает алфавиты (например, KAZ/KAZA в русских буквах).
        """
        return text.translate(self.cyr_to_lat_map).upper()

    def preprocess_image_for_ocr(self, image_path: str) -> str:
        """
        Препроцессинг изображения для улучшения качества OCR:
        - Upscaling (увеличение разрешения в 2x)
        - Увеличение контраста
        - Увеличение резкости
        - PIL препроцессинг (более мягкий, лучше для MRZ)
        """
        try:
            # Используем PIL препроцессинг (работает лучше для MRZ строк)
            # OpenCV препроцессинг слишком агрессивный и может "съедать" тонкие MRZ символы
            return self._preprocess_with_pil(image_path)

        except Exception as e:
            if self.debug:
                print(f"⚠️ Ошибка препроцессинга: {e}")
            return image_path  # Возвращаем оригинал при ошибке

    def _preprocess_with_opencv(self, image_path: str) -> str:
        """Продвинутый препроцессинг с OpenCV"""
        # Читаем изображение
        img = cv2.imread(image_path)
        if img is None:
            return self._preprocess_with_pil(image_path)

        height, width = img.shape[:2]

        # 1. Upscaling - увеличиваем в 2 раза
        img = cv2.resize(img, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

        # 2. Конвертируем в grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Легкое шумоподавление + CLAHE (без жесткой бинаризации)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # 4. Deskew отключен (метод _deskew_binary не реализован)
        # Если нужно добавить deskew, реализуйте метод _deskew_binary
        # _, deskew_binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # deskewed, angle = self._deskew_binary(deskew_binary)
        # if angle and self.debug:
        #     print(f"  ↩️ Deskew применен: угол {angle:.2f}°")
        # if angle:
        #     (h, w) = enhanced.shape[:2]
        #     center = (w // 2, h // 2)
        #     M = cv2.getRotationMatrix2D(center, angle, 1.0)
        #     enhanced = cv2.warpAffine(
        #         enhanced, M, (w, h),
        #         flags=cv2.INTER_CUBIC,
        #         borderMode=cv2.BORDER_REPLICATE
        #     )

        # 5. Легкая резкость (без агрессивной бинаризации)
        kernel_sharpen = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)

        # Сохраняем
        preprocessed_path = image_path.rsplit('.', 1)[0] + '_preprocessed.jpg'
        cv2.imwrite(preprocessed_path, sharpened, [cv2.IMWRITE_JPEG_QUALITY, 95])

        if self.debug:
            print(f"✨ OpenCV препроцессинг: {width}x{height} -> {width*2}x{height*2}, denoise+CLAHE, лёгкая резкость")

        return preprocessed_path

    def _preprocess_with_pil(self, image_path: str) -> str:
        """
        Оптимизированный препроцессинг с PIL

        ОПТИМИЗАЦИИ ДЛЯ СКОРОСТИ:
        - Upscaling 1.3x вместо 2x (пикселей в 1.69x раз вместо 4x)
        - Резкость 1.5x вместо 2.0x + убран дополнительный SHARPEN
        - Это ускоряет обработку в ~2.5 раза при сохранении качества OCR
        """
        img = Image.open(image_path)

        # Конвертируем в RGB если нужно
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 1. Умеренный upscaling - 1.3x вместо 2x (экономия скорости ~2.5x)
        width, height = img.size
        new_width = int(width * 1.3)
        new_height = int(height * 1.3)
        img = img.resize((new_width, new_height), Image.LANCZOS)

        # 2. Увеличение контраста (1.5x - оставляем без изменений)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # 3. Умеренная резкость (1.5x вместо 2.0x + убираем дополнительный SHARPEN)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)

        # Сохраняем во временный файл
        preprocessed_path = image_path.rsplit('.', 1)[0] + '_preprocessed.jpg'
        img.save(preprocessed_path, 'JPEG', quality=95)

        if self.debug:
            print(f"✨ PIL препроцессинг (оптимизированный): {width}x{height} -> {new_width}x{new_height}, контраст +50%, резкость +50%")

        return preprocessed_path

    def validate_iin_checksum(self, iin: str) -> bool:
        """Проверка контрольной суммы ИИН"""
        if not iin or len(iin) != 12 or not iin.isdigit():
            return False
        weights1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        checksum = sum(int(iin[i]) * weights1[i] for i in range(11)) % 11
        if checksum == 10:
            weights2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]
            checksum = sum(int(iin[i]) * weights2[i] for i in range(11)) % 11
        return checksum == int(iin[11])

    def get_gender_from_iin(self, iin: str) -> str:
        if not iin or len(iin) != 12:
            return ""
        digit = int(iin[6])
        return "M" if digit in [1, 3, 5] else "F" if digit in [2, 4, 6] else ""

    def extract_date_from_iin(self, iin: str) -> str:
        if not iin or len(iin) < 6:
            return ""
        try:
            yy, mm, dd = int(iin[0:2]), int(iin[2:4]), int(iin[4:6])
            century_digit = int(iin[6]) if len(iin) > 6 else 0
            if century_digit in [1, 2]:
                year = 1800 + yy
            elif century_digit in [3, 4]:
                year = 1900 + yy
            elif century_digit in [5, 6]:
                year = 2000 + yy
            else:
                year = 1900 + yy
            datetime(year, mm, dd)
            return f"{dd:02d}.{mm:02d}.{year}"
        except:
            return ""

    def extract_text_easyocr(self, file_path: str) -> str:
        """Извлечение текста с EasyOCR с автоповоротом"""
        temp_file = None
        preprocessed_file = None
        try:
            original_file = file_path

            # Конвертируем PDF в изображение
            if file_path.lower().endswith('.pdf'):
                if self.debug:
                    print(f"📄 Конвертация PDF -> JPEG")
                pages = convert_from_path(file_path, dpi=300, poppler_path=self.poppler_path)
                if not pages:
                    return ""
                temp_img = file_path.replace('.pdf', '_temp.jpg')
                pages[0].save(temp_img, 'JPEG', quality=95)
                file_path = temp_img
                temp_file = temp_img
                if self.debug:
                    print(f"✅ PDF конвертирован: {temp_img}")
            # Конвертируем PNG/другие форматы в JPEG для лучшей совместимости
            elif not file_path.lower().endswith(('.jpg', '.jpeg')):
                if self.debug:
                    print(f"🖼️ Конвертация {file_path.split('.')[-1].upper()} -> JPEG")
                try:
                    img = Image.open(file_path)
                    # Конвертируем в RGB если нужно
                    if img.mode != 'RGB':
                        if self.debug:
                            print(f"🔄 Конвертация {img.mode} -> RGB")
                        img = img.convert('RGB')
                    temp_jpg = file_path.rsplit('.', 1)[0] + '_temp_ocr.jpg'
                    img.save(temp_jpg, 'JPEG', quality=95)
                    img.close()  # 🔥 ВАЖНО: закрываем файл до удаления
                    file_path = temp_jpg
                    temp_file = temp_jpg
                    if self.debug:
                        print(f"✅ Изображение конвертировано: {temp_jpg}")
                except Exception as e:
                    print(f"❌ Ошибка конвертации изображения: {e}")
                    # Пробуем использовать оригинальный файл
                    file_path = original_file

            # Применяем препроцессинг для улучшения качества OCR
            preprocessed_path = self.preprocess_image_for_ocr(file_path)
            preprocessed_file = preprocessed_path if preprocessed_path != file_path else None

            # EasyOCR на обработанном изображении
            result = self.reader.readtext(preprocessed_path)

            # Проверка качества распознавания
            valid_texts = [text for (bbox, text, confidence) in result if confidence > 0.3 and len(text) > 2]

            # Если распознано мало текста (<5 слов), пробуем повернуть
            if len(valid_texts) < 5:
                if self.debug:
                    print(f"⚠️ Мало текста распознано ({len(valid_texts)} слов), пробуем повороты...")

                best_result = result
                best_count = len(valid_texts)
                best_rotation = 0

                # Пробуем повороты
                img = Image.open(preprocessed_path)
                for rotation in [90, 180, 270]:
                    # Поворачиваем
                    rotated_img = img.rotate(rotation, expand=True)
                    rotated_path = preprocessed_path.rsplit('.', 1)[0] + f'_rot{rotation}.jpg'
                    rotated_img.save(rotated_path, 'JPEG', quality=95)

                    # Распознаем
                    rotated_result = self.reader.readtext(rotated_path)
                    rotated_valid = [text for (bbox, text, confidence) in rotated_result if confidence > 0.3 and len(text) > 2]

                    # Удаляем временный файл
                    os.remove(rotated_path)

                    # Если лучше - сохраняем
                    if len(rotated_valid) > best_count:
                        best_result = rotated_result
                        best_count = len(rotated_valid)
                        best_rotation = rotation
                        if self.debug:
                            print(f"  ✅ Поворот {rotation}° лучше: {len(rotated_valid)} слов")

                result = best_result
                if best_rotation > 0 and self.debug:
                    print(f"🔄 Использован поворот {best_rotation}°")

            # Собираем текст
            text_lines = []
            for (bbox, text, confidence) in result:
                # Понижаем порог для лучшего распознавания
                if confidence > 0.3:
                    text_lines.append(text)

            full_text = "\n".join(text_lines)

            if self.debug:
                print("="*60)
                print("📄 EASYOCR TEXT:")
                print(full_text)
                print("="*60)

            return full_text

        except Exception as e:
            if self.debug:
                print(f"❌ Ошибка EasyOCR: {e}")
            return ""

        finally:
            # 🔥 КРИТИЧЕСКИ ВАЖНО: Очищаем временные файлы в любом случае
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    if self.debug:
                        print(f"🗑️ Удален временный файл: {temp_file}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить {temp_file}: {e}")

            if preprocessed_file and os.path.exists(preprocessed_file):
                try:
                    os.remove(preprocessed_file)
                    if self.debug:
                        print(f"🗑️ Удален preprocessed файл: {preprocessed_file}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить {preprocessed_file}: {e}")

    def extract_mrz_passporteye(self, file_path: str) -> Optional[dict]:
        """Извлечение MRZ с PassportEye"""
        if not HAS_PASSPORTEYE or read_mrz is None:
            if self.debug:
                print("⚠️ PassportEye недоступен (нет зависимости).")
            return None
        try:
            if file_path.lower().endswith('.pdf'):
                pages = convert_from_path(file_path, dpi=300, poppler_path=self.poppler_path)
                if not pages:
                    return None
                temp_img = file_path.replace('.pdf', '_temp_mrz.jpg')
                pages[0].save(temp_img, 'JPEG')
                file_path = temp_img

            mrz_data = read_mrz(file_path)

            if '_temp_mrz.jpg' in file_path:
                os.remove(file_path)

            if not mrz_data or not mrz_data.mrz_type:
                return None

            result = {}
            if mrz_data.names:
                result['first_name'] = mrz_data.names
            if mrz_data.surname:
                result['last_name'] = mrz_data.surname
            if mrz_data.number:
                result['document_number'] = mrz_data.number
            if mrz_data.date_of_birth:
                result['dob'] = mrz_data.date_of_birth
            if mrz_data.expiration_date:
                result['expiration_date'] = mrz_data.expiration_date
            if mrz_data.sex:
                result['gender'] = mrz_data.sex
            if mrz_data.nationality:
                result['nationality'] = mrz_data.nationality

            if self.debug:
                print("="*60)
                print("📋 PASSPORTEYE MRZ DATA:")
                print(result)
                print("="*60)

            return result

        except Exception as e:
            if self.debug:
                print(f"⚠️ PassportEye: {e}")
            return None

    def validate_mrz_name(self, name: str, field_name: str = "name") -> bool:
        """
        Проверка качества одного имени/фамилии из MRZ
        Возвращает True если имя валидно, False если это мусор
        """
        if not name:
            return True  # Пустое имя - не критично

        # Проверка 1: Слишком много повторяющихся символов (C, O, E, G, S)
        # "SOOCCOCGCECCCOCG..." - явный мусор
        garbage_chars = name.count('C') + name.count('O') + name.count('E') + name.count('G') + name.count('S')
        if len(name) > 0 and (garbage_chars / len(name)) > 0.5:
            if self.debug:
                print(f"⚠️ MRZ {field_name} отклонено: слишком много мусорных символов ({garbage_chars}/{len(name)})")
            return False

        # Проверка 2: Слишком длинное имя без пробелов (>20 символов)
        # "RAYAKXALTYBAEVNA" - имя+отчество слитно
        clean_name = name.replace(' ', '').replace('<', '')
        if len(clean_name) > 20:
            if self.debug:
                print(f"⚠️ MRZ {field_name} отклонено: слишком длинное ({len(clean_name)} символов)")
            return False

        return True

    def validate_document_number(self, doc_num: str) -> bool:
        """Валидация номера документа - отклоняем мусор вроде <<<<<6<<<"""
        if not doc_num:
            return False

        # Проверка 1: Слишком много символов '<' (мусор из MRZ)
        bracket_count = doc_num.count('<')
        if len(doc_num) > 0 and (bracket_count / len(doc_num)) > 0.5:
            if self.debug:
                print(f"⚠️ Номер документа отклонен: слишком много '<' символов ({bracket_count}/{len(doc_num)})")
            return False

        # Проверка 2: Должен содержать хотя бы несколько цифр или букв
        alphanumeric = sum(c.isalnum() for c in doc_num)
        if alphanumeric < 3:
            if self.debug:
                print(f"⚠️ Номер документа отклонен: слишком мало значимых символов ({alphanumeric})")
            return False

        return True

    def validate_date(self, date_str: str) -> bool:
        """Валидация даты - отклоняем мусор вроде EVA<<K"""
        if not date_str:
            return False

        # Проверка 1: Слишком много символов '<' (мусор из MRZ)
        bracket_count = date_str.count('<')
        if len(date_str) > 0 and (bracket_count / len(date_str)) > 0.3:
            if self.debug:
                print(f"⚠️ Дата отклонена: слишком много '<' символов ({bracket_count}/{len(date_str)})")
            return False

        # Проверка 2: Должна содержать хотя бы несколько цифр
        digit_count = sum(c.isdigit() for c in date_str)
        if digit_count < 4:  # Минимум 4 цифры для даты
            if self.debug:
                print(f"⚠️ Дата отклонена: слишком мало цифр ({digit_count})")
            return False

        # Проверка 3: Не должна содержать много букв
        letter_count = sum(c.isalpha() for c in date_str)
        if letter_count > 2:  # Максимум 2 буквы (например, разделители)
            if self.debug:
                print(f"⚠️ Дата отклонена: слишком много букв ({letter_count})")
            return False

        return True

    def validate_mrz_data(self, mrz_data: dict) -> bool:
        """Проверка качества MRZ данных от PassportEye"""
        if not mrz_data:
            return False

        # Проверяем фамилию
        last_name = mrz_data.get('last_name', '')
        if last_name and not self.validate_mrz_name(last_name, "last_name"):
            return False

        # Проверяем имя
        first_name = mrz_data.get('first_name', '')
        if first_name and not self.validate_mrz_name(first_name, "first_name"):
            return False

        # Проверка даты рождения: должна быть в формате DD.MM.YYYY или близко к нему
        dob = mrz_data.get('dob', '')
        if dob:
            # Сначала проверяем общую валидность даты
            if not self.validate_date(dob):
                return False
            # Дополнительно проверяем формат
            if not re.match(r'\d{2}[./]\d{2}[./]\d{4}', dob):
                # Разрешаем только если это похоже на дату (6 цифр подряд)
                if not re.search(r'\d{6}', dob):
                    return False

        # Проверка срока действия
        exp_date = mrz_data.get('expiration_date', '')
        if exp_date and not self.validate_date(exp_date):
            return False

        # Проверка пола: должен быть M или F
        gender = mrz_data.get('gender', '')
        if gender and gender not in ['M', 'F']:
            return False

        # Проверка номера документа
        doc_num = mrz_data.get('document_number', '')
        if doc_num and not self.validate_document_number(doc_num):
            return False

        return True

    def detect_document_type(self, text: str) -> str:
        """
        Определение типа документа по ключевым словам
        Возвращает: "passport" или "id_card"
        """
        text_upper = text.upper()

        # Ключевые слова для удостоверения личности
        id_card_keywords = [
            'IDENTITY CARD',
            'ЖЕКЕ КУӘЛІК',
            'ЖЕКЕ КУӘЛIГI',
            'ЖЕКЕ КУАЛIК',
            'КУӘЛІК',
            'КУАЛIК',
            'IDENTITY',
        ]

        # Ключевые слова для паспорта
        passport_keywords = [
            'PASSPORT',
            'ПАСПОРТ',
            'ПАСПОРТА',
        ]

        # Проверяем на ID card
        for keyword in id_card_keywords:
            if keyword in text_upper:
                if self.debug:
                    print(f"🆔 Обнаружено удостоверение личности (ключевое слово: {keyword})")
                return "id_card"

        # Проверяем на паспорт
        for keyword in passport_keywords:
            if keyword in text_upper:
                if self.debug:
                    print(f"📘 Обнаружен паспорт (ключевое слово: {keyword})")
                return "passport"

        # По умолчанию считаем паспортом
        if self.debug:
            print(f"❓ Тип документа не определен, считаем паспортом")
        return "passport"

    def parse_text_fields(self, text: str) -> PassportData:
        """Парсинг полей из текста"""
        data = PassportData()

        def normalize_date_sep(value: str) -> str:
            return value.replace(',', '.').replace('/', '.')

        # Определяем тип документа
        data.document_type = self.detect_document_type(text)

        # ИИН / ПИНФЛ (12-14 цифр)
        iin_match = re.search(r'\b(\d{12,14})\b', text)
        if iin_match:
            iin = iin_match.group(1)
            # Проверяем контрольную сумму только для 12-значных ИИН
            if len(iin) == 12 and self.validate_iin_checksum(iin):
                data.iin = iin
                data.gender = self.get_gender_from_iin(iin)
                data.dob = self.extract_date_from_iin(iin)
            else:
                data.iin = iin  # сохраняем даже без checksum (для 13-14 цифр)

        # Номер документа - ищем N и цифры, или буквы+цифры (узбекские паспорта FA1415473)
        doc_patterns = [
            r'N\s*(\d{8,9})',  # N16210280 (казахские)
            r'№\s*(\d{8,9})',  # № 16210280
            r'\b([A-Z]{2}\d{7})\b',  # FA1415473 (узбекские, киргизские)
        ]
        for pattern in doc_patterns:
            doc_match = re.search(pattern, text, re.IGNORECASE)
            if doc_match:
                doc_num = doc_match.group(1)
                # Если начинается с цифр, добавляем N
                if doc_num[0].isdigit():
                    candidate = "N" + doc_num
                else:
                    candidate = doc_num
                # Валидируем перед сохранением
                if self.validate_document_number(candidate):
                    data.document_number = candidate
                    break

        # Служебные слова, которые нужно игнорировать
        EXCLUDE_WORDS = {
            'TYPI', 'TYPE', 'PASSPORT', 'CODE', 'STATE', 'GIVEN', 'NAMES',
            'GIVENNAMES', 'DATE', 'BIRTH', 'PLACE', 'ISSUE', 'EXPIRY',
            'AUTHORITY', 'MINISTRY', 'INTERNAL', 'AFFAIRS', 'KAZAKHSTAN',
            'КАЗАХСТАН', 'ПАСПОРТ', 'DATEOFBIRTH', 'PLACEOFBIRTH',
            'DATEOFISSUE', 'DATEOFEXPIRY', 'AUHORIY', 'CODEOFSTATE',
            'FLACE', 'QFEFT', 'OF', 'PASPPORT'
        }

        # Коды стран, которые нужно удалить из фамилии (если приклеились из-за OCR)
        COUNTRY_CODES = [
            'KAZ', 'UZB', 'KGZ', 'TJK', 'TKM', 'RUS', 'AZE', 'ARM', 'GEO',
            'BLR', 'UKR', 'MDA', 'USA', 'GBR', 'CAN', 'AUS', 'TUR', 'CHN',
            'IND', 'PAK', 'AFG', 'IRN', 'IRQ', 'SAU', 'ARE', 'QAT', 'KWT'
        ]
        COUNTRY_CODE_HEURISTICS = {'KAZ', 'UZB', 'KGZ', 'TJK', 'TKM'}

        # Фамилия - ищем латиницу после английского слова или перед именем

        # Паттерн 1 (ПРИОРИТЕТ): MRZ строка (самый надежный источник, с учетом пробелов)
        # Формат MRZ: P<CCC<SURNAME_PARTS<<FIRSTNAME где CCC - код страны (3 буквы)
        # Фамилия может содержать несколько частей: AKHME<J<ANOV или с пробелами AKHME J ANOV

        # Правильный паттерн для MRZ: P<CCCSURNAME<<FIRSTNAME
        # Формат: P< + код страны (3 буквы) + фамилия + << + имя
        # Важно: между кодом страны и фамилией НЕТ символа <
        # Поддерживаем пробелы после <<: "P<KAZMUKHAMBETKALIYEVA<< D INARA"
        # Имя может содержать пробелы: захватываем всё до символов < или конца
        mrz_surname = re.search(r'P<([A-Z]{3})([A-Z<]+?)<<\s*([A-Z\s]+?)(?:<|$)', text)

        # ПРИОРИТЕТ 2: Вариант БЕЗ кода страны (просто SURNAME<<FIRSTNAME)
        # Этот паттерн ДОЛЖЕН быть ДО паттерна с кодом страны, иначе первые 3 буквы фамилии
        # будут ошибочно приняты за код страны (SAU-RBAYEV вместо SAURBAYEV)
        # Пример: SAURBAYEV<<RUSLAN или AKHMOLDAYEVA< <ALTYNSHASH
        if not mrz_surname:
            # Поддерживаем разделитель << или < < (с пробелом)
            # Имя может содержать пробелы
            mrz_surname = re.search(r'\b([A-Z]{4,})<\s*<\s*([A-Z\s]+?)(?:<|$)', text)

        # ПРИОРИТЕТ 3: Упрощенный вариант (без P<, но с кодом страны)
        # Используется только если предыдущие не сработали
        # Пример: KAZAKHMOLDAYEVA<<ALTYNSHASH (где KAZ - код страны)
        if not mrz_surname:
            # Этот паттерн опасный - может съесть первые 3 буквы фамилии
            # Поэтому проверяем что первые 3 буквы - известный код страны
            potential_match = re.search(r'\b([A-Z]{3})([A-Z<]+?)<<([A-Z\s]+)', text)
            if potential_match:
                potential_code = potential_match.group(1)
                # Проверяем что это реальный код страны
                if potential_code in COUNTRY_CODES:
                    mrz_surname = potential_match

        if mrz_surname:
            # Определяем, какая попытка сработала
            if len(mrz_surname.groups()) == 3:
                # Приоритет 1 или 3: есть код страны
                # P<CCC<SURNAME<<FIRSTNAME (приоритет 1)
                # CCC<SURNAME<<FIRSTNAME где CCC проверен как код страны (приоритет 3)
                country_code = mrz_surname.group(1)
                surname_raw = mrz_surname.group(2)
                firstname_raw = mrz_surname.group(3)
            elif len(mrz_surname.groups()) == 2:
                # Приоритет 2: нет кода страны (SURNAME<<FIRSTNAME или SURNAME< <FIRSTNAME)
                country_code = None
                surname_raw = mrz_surname.group(1)
                firstname_raw = mrz_surname.group(2)
            else:
                # Неожиданное количество групп - пропускаем MRZ
                if self.debug:
                    print(f"⚠️ MRZ: неожиданное количество групп ({len(mrz_surname.groups())}), пропускаем")
                surname_raw = None
                firstname_raw = None

            # Обрабатываем только если удалось извлечь данные
            if surname_raw and firstname_raw:
                # Очищаем фамилию: удаляем < и пробелы полностью (AKHME J ANOV -> AKHMEJANOV)
                surname = re.sub(r'[<\s]+', '', surname_raw).strip()

                # Очищаем имя:
                # 1. Заменяем < на пробелы (JOHN<PAUL -> JOHN PAUL)
                # 2. Удаляем повторяющиеся пробелы
                # 3. Оставляем только первое слово (имя без отчества), если остальное выглядит как мусор
                firstname = re.sub(r'<', ' ', firstname_raw).strip()
                firstname = re.sub(r'\s+', ' ', firstname)  # Удаляем повторяющиеся пробелы

                # Если имя содержит несколько слов, проверяем качество
                firstname_parts = firstname.split()
                if len(firstname_parts) > 1:
                    # Если второе слово короткое (1-2 символа) или содержит lowercase - вероятно это мусор
                    main_name = firstname_parts[0]
                    other_parts = firstname_parts[1:]
                    # Оставляем дополнительные части только если они валидные (длина >= 3 и все uppercase)
                    valid_parts = [main_name]
                    for part in other_parts:
                        if len(part) >= 3 and part.isupper() and part.isalpha():
                            valid_parts.append(part)
                    firstname = ' '.join(valid_parts)

                # 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Удаляем коды стран из начала фамилии
                # Проблема: OCR может слить "P<KAZ<AKHMETOV" в "KAZAKHMETOV"

                # Случай 1: Явный код страны из regex (самый надежный)
                if country_code:
                    if surname.startswith(country_code):
                        surname = surname[len(country_code):]
                        if self.debug:
                            print(f"🔧 Удален явный код страны '{country_code}' из фамилии -> {surname}")
                else:
                    # Иногда OCR возвращает страну в начале фамилии (например KAZMUKHAMBETKALIYEVA)
                    # – удаляем только центрально-азиатские коды и только если следующий символ согласный.
                    consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
                    potential_surname_starts = {'KAZA', 'UZBE', 'KGZA', 'RUSA', 'TKMA', 'TKME'}
                    for code in COUNTRY_CODE_HEURISTICS:
                        if surname.startswith(code) and len(surname) > len(code) + 4:
                            next_char = surname[len(code)]
                            combined = (code + next_char).upper()
                            if next_char in consonants and combined not in potential_surname_starts:
                                old_surname = surname
                                surname = surname[len(code):]
                                if self.debug:
                                    print(f"🔧 Удален код '{code}' (после него согласная '{next_char}'): {old_surname} -> {surname}")
                                break

                # Проверяем, что это не мусор
                if surname and firstname and surname not in EXCLUDE_WORDS and firstname not in EXCLUDE_WORDS:
                    data.last_name = surname
                    data.first_name = firstname
                    if self.debug:
                        print(f"✅ MRZ: Фамилия='{surname}', Имя='{firstname}'")

        # Паттерн 2: Узбекские паспорта (FAMILIYASI/SURNAME, ISMI/GIVEN NAMES)
        # Поддерживаем многословные имена: ([A-Z\s]+) вместо ([A-Z]+)
        if not data.last_name:
            uzb_surname = re.search(r'(?:FAMILIYASI|SURNAME)[^\n]*\n\s*([A-Z\s]+)', text, re.IGNORECASE)
            uzb_firstname = re.search(r'(?:ISMI|GIVEN NAMES)[^\n]*\n\s*([A-Z\s]+)', text, re.IGNORECASE)
            if uzb_surname and uzb_firstname:
                surname = uzb_surname.group(1).strip()
                firstname = uzb_firstname.group(1).strip()

                # Фильтруем служебные слова из имени/фамилии
                # Разбиваем на слова и удаляем служебные
                surname_words = [w for w in surname.split() if w not in EXCLUDE_WORDS and w not in COUNTRY_CODES]
                firstname_words = [w for w in firstname.split() if w not in EXCLUDE_WORDS and w not in COUNTRY_CODES]

                # Оставляем только первое слово для фамилии, первое слово для имени
                surname = surname_words[0] if surname_words else surname.split()[0]
                firstname = firstname_words[0] if firstname_words else firstname.split()[0]

                # Удаляем коды стран если они попали в начало (на случай ошибок OCR)
                for code in COUNTRY_CODES:
                    if surname.startswith(code + ' ') or surname.startswith(code):
                        # Проверяем что это не часть многословной фамилии
                        parts = surname.split()
                        if len(parts) > 1 and parts[0] == code:
                            surname = ' '.join(parts[1:])
                            if self.debug:
                                print(f"🔧 Удален код страны '{code}' из узбекской фамилии -> {surname}")
                            break
                        elif surname.startswith(code) and len(surname) > len(code) + 3:
                            surname = surname[len(code):].strip()
                            if self.debug:
                                print(f"🔧 Удален код страны '{code}' из узбекской фамилии -> {surname}")
                            break

                if surname not in EXCLUDE_WORDS and firstname not in EXCLUDE_WORDS:
                    data.last_name = surname
                    data.first_name = firstname
                    if self.debug:
                        print(f"✅ Узбекский паспорт: Фамилия='{surname}', Имя='{firstname}'")

        # Паттерн 3: Обычный текст (последний приоритет)
        if not data.last_name:
            lines = text.split('\n')
            # Сначала пробуем две соседние строки (фамилия / имя на разных строках)
            for i in range(len(lines) - 1):
                line1 = lines[i].upper()
                line2 = lines[i + 1].upper()
                w1 = re.findall(r'\b([A-Z]{3,})\b', line1)
                w2 = re.findall(r'\b([A-Z]{3,})\b', line2)
                w1 = [w for w in w1 if w not in EXCLUDE_WORDS and w not in COUNTRY_CODES]
                w2 = [w for w in w2 if w not in EXCLUDE_WORDS and w not in COUNTRY_CODES]
                if len(w1) >= 1 and len(w2) >= 1:
                    data.last_name = w1[0]
                    data.first_name = w2[0]
                    if self.debug:
                        print(f"✅ Обычный текст (2 строки): Фамилия='{data.last_name}', Имя='{data.first_name}'")
                    break

            # Если не нашли — берем две латинские в одной строке
            if not data.last_name:
                for line in lines:
                    line_up = line.upper()
                    latin_words = re.findall(r'\b([A-Z]{3,})\b', line_up)
                    latin_words = [w for w in latin_words if w not in EXCLUDE_WORDS and w not in COUNTRY_CODES]
                    if len(latin_words) >= 2:
                        data.last_name = latin_words[0]
                        data.first_name = latin_words[1]
                        if self.debug:
                            print(f"✅ Обычный текст: Фамилия='{data.last_name}', Имя='{data.first_name}'")
                        break

        # Дата рождения
        if not data.dob:
            # Формат DD.MM.YYYY или с запятой
            dob_match = re.search(r'\b(\d{2}[.,]\d{2}[.,]\d{4})\b', text)
            if dob_match:
                data.dob = normalize_date_sep(dob_match.group(1))
            else:
                # Формат "DD MM YYYY" (узбекские паспорта)
                dob_match = re.search(r'(?:DATE\s*OF\s*BIRTH|DNEOF\s*BIRTH)[^\d]*(\d{2})\s+(\d{2})\s+(\d{4})', text, re.IGNORECASE)
                if dob_match:
                    dd, mm, yyyy = dob_match.groups()
                    data.dob = f"{dd}.{mm}.{yyyy}"

        # Срок действия - обычно последняя дата
        date_matches = re.findall(r'\b(\d{2}[.,]\d{2}[.,]\d{4})\b', text)
        normalized_dates = [normalize_date_sep(d) for d in date_matches]
        if len(normalized_dates) >= 2:
            data.expiration_date = normalized_dates[-1]  # Последняя дата

        # Пол - УСИЛЕННОЕ РАСПОЗНАВАНИЕ (обязательное поле!)
        if not data.gender:
            # Паттерн 1: После SEX/ЖЫНЫСЫ
            gender_match = re.search(r'(?:SEX|ЖЫНЫСЫ)[:\s]*([МЖ/MF])', text, re.IGNORECASE)
            if gender_match:
                g = gender_match.group(1).upper()
                data.gender = "M" if g in ['M', 'М'] else "F" if g in ['F', 'Ж'] else ""

        if not data.gender:
            # Паттерн 2: Одиночная буква M/F/М/Ж на отдельной строке или после пробелов
            gender_match = re.search(r'\b([МЖ]|[MF])\b', text, re.IGNORECASE)
            if gender_match:
                g = gender_match.group(1).upper()
                data.gender = "M" if g in ['M', 'М'] else "F" if g in ['F', 'Ж'] else ""

        if not data.gender:
            # Паттерн 3: Ищем "MALE" или "FEMALE"
            if re.search(r'\bMALE\b', text, re.IGNORECASE):
                data.gender = "M"
            elif re.search(r'\bFEMALE\b', text, re.IGNORECASE):
                data.gender = "F"

        # Национальность
        if not data.nationality:
            # Ищем UZBEKISTAN, KAZAKHSTAN и т.д.
            nationality_match = re.search(r'\b(UZBEKISTAN|KAZAKHSTAN|KYRGYZSTAN|TAJIKISTAN|TURKMENISTAN)\b', text, re.IGNORECASE)
            if nationality_match:
                country = nationality_match.group(1).upper()
                # Конвертируем в код страны
                nationality_map = {
                    'UZBEKISTAN': 'UZB',
                    'KAZAKHSTAN': 'KAZ',
                    'KYRGYZSTAN': 'KGZ',
                    'TAJIKISTAN': 'TJK',
                    'TURKMENISTAN': 'TKM'
                }
                data.nationality = nationality_map.get(country, 'KAZ')

        # Телефон
        phone_match = re.search(r'(?:\+7|8)\s?\(?\d{3}\)?\s?\d{3}[\s-]?\d{2}[\s-]?\d{2}', text)
        if phone_match:
            data.phone = phone_match.group(0)

        return data

    def parse(self, file_path: str) -> PassportData:
        """Главный метод парсинга"""
        if self.debug:
            print(f"\n🔍 Парсинг файла: {file_path}")

        # 1. PassportEye ОТКЛЮЧЕН (потребляет много памяти и дает мусорные данные)
        # mrz_data = self.extract_mrz_passporteye(file_path)
        mrz_data = None

        # 2. EasyOCR для текста
        raw_text = self.extract_text_easyocr(file_path)
        text = self.normalize_text(raw_text)

        # 3. Парсим текст (уже нормализованный)
        data = self.parse_text_fields(text)

        # 4. Сохраняем оригинальные имена из EasyOCR (до применения MRZ)
        easyocr_last_name = data.last_name
        easyocr_first_name = data.first_name

        # 5. MRZ переопределяет (приоритет) - используем выборочно
        if mrz_data:
            # Сохраняем MRZ имена отдельно для booking_handlers.py
            if mrz_data.get('last_name'):
                data.mrz_last_name = mrz_data['last_name']
            if mrz_data.get('first_name'):
                data.mrz_first_name = mrz_data['first_name']

            # Проверяем валидность всех MRZ данных
            mrz_valid = self.validate_mrz_data(mrz_data)

            if mrz_valid:
                # Все MRZ данные валидны - используем все
                if self.debug:
                    print("✅ MRZ данные прошли валидацию, используем их")
                if mrz_data.get('last_name'):
                    data.last_name = mrz_data['last_name']
                if mrz_data.get('first_name'):
                    data.first_name = mrz_data['first_name']
                if mrz_data.get('document_number'):
                    data.document_number = mrz_data['document_number']
                if mrz_data.get('dob'):
                    data.dob = mrz_data['dob']
                if mrz_data.get('expiration_date'):
                    data.expiration_date = mrz_data['expiration_date']
                if mrz_data.get('gender'):
                    data.gender = mrz_data['gender']
                if mrz_data.get('nationality'):
                    data.nationality = mrz_data['nationality']
            else:
                # MRZ не прошла полную валидацию, но берем отдельные валидные поля
                if self.debug:
                    print("⚠️ MRZ данные не прошли полную валидацию, используем выборочно")

                # Документ - берем если пустой в EasyOCR и валиден
                if not data.document_number and mrz_data.get('document_number'):
                    mrz_doc = mrz_data['document_number']
                    if self.validate_document_number(mrz_doc):
                        data.document_number = mrz_doc

                # Дата рождения - берем если пустая в EasyOCR и валидна
                if not data.dob and mrz_data.get('dob'):
                    mrz_dob = mrz_data['dob']
                    # Проверяем валидность и формат
                    if self.validate_date(mrz_dob) and re.match(r'\d{6}', mrz_dob):
                        data.dob = mrz_dob

                # Пол - берем если пустой в EasyOCR и валиден (M или F)
                if not data.gender and mrz_data.get('gender') in ['M', 'F']:
                    data.gender = mrz_data['gender']

                # Национальность - берем если пустая в EasyOCR
                if not data.nationality and mrz_data.get('nationality'):
                    data.nationality = mrz_data['nationality']

                # Срок действия - берем если пустой и валиден
                if not data.expiration_date and mrz_data.get('expiration_date'):
                    mrz_exp = mrz_data['expiration_date']
                    if self.validate_date(mrz_exp):
                        data.expiration_date = mrz_exp

        # 6. ГИБКАЯ ПРИОРИТИЗАЦИЯ: если EasyOCR нашел четкое короткое имя,
        # а MRZ содержит длинное (имя+отчество слитно), используем EasyOCR
        if easyocr_first_name and data.first_name:
            # Если EasyOCR имя существенно короче MRZ имени (>5 символов разница)
            # И EasyOCR имя не слишком короткое (>2 символов)
            if len(easyocr_first_name) > 2 and len(data.first_name) - len(easyocr_first_name) > 5:
                if self.debug:
                    print(f"🔄 Приоритизируем EasyOCR имя '{easyocr_first_name}' вместо MRZ '{data.first_name}'")
                data.first_name = easyocr_first_name

        if easyocr_last_name and data.last_name:
            # То же самое для фамилии
            if len(easyocr_last_name) > 2 and len(data.last_name) - len(easyocr_last_name) > 5:
                if self.debug:
                    print(f"🔄 Приоритизируем EasyOCR фамилию '{easyocr_last_name}' вместо MRZ '{data.last_name}'")
                data.last_name = easyocr_last_name

        # 7. ФИНАЛЬНАЯ ПРОВЕРКА ПОЛА - обязательное поле!
        if not data.gender:
            # Fallback: пытаемся определить по имени (распространенные имена)
            if data.first_name:
                name_lower = data.first_name.lower()
                # Женские окончания
                female_endings = ['a', 'ya', 'ia', 'na', 'ra', 'la', 'ma', 'ta', 'sa']
                # Распространенные женские имена
                female_names = {'aisha', 'aiman', 'ainur', 'aiya', 'akmaral', 'aliya', 'alma', 'altynai',
                                'anar', 'asem', 'asiya', 'aygerim', 'aynur', 'azhar', 'diana', 'dinara',
                                'farida', 'fatima', 'gaukhar', 'gulnara', 'gulzhan', 'indira', 'kamila',
                                'karlygash', 'karina', 'kulyaim', 'laura', 'madina', 'malika', 'mariam',
                                'nazira', 'raya', 'saule', 'symbat', 'togzhan', 'ulzhan', 'zarina', 'zhanna'}

                # Проверяем по окончанию
                if any(name_lower.endswith(ending) for ending in female_endings):
                    data.gender = "F"
                    if self.debug:
                        print(f"🔄 Пол определен по окончанию имени '{data.first_name}': F")
                # Проверяем по списку известных женских имен
                elif name_lower in female_names:
                    data.gender = "F"
                    if self.debug:
                        print(f"🔄 Пол определен по базе имен '{data.first_name}': F")
                else:
                    # По умолчанию - мужской
                    data.gender = "M"
                    if self.debug:
                        print(f"⚠️ Пол не распознан, используем по умолчанию: M")
            else:
                # Совсем нет данных - по умолчанию мужской
                data.gender = "M"
                if self.debug:
                    print(f"⚠️ Пол не распознан (нет имени), используем по умолчанию: M")

        # 8. Валидация номера документа - отклоняем мусор
        if data.document_number and not self.validate_document_number(data.document_number):
            if self.debug:
                print(f"❌ Номер документа '{data.document_number}' не прошел валидацию, сбрасываем")
            data.document_number = ""

        # 9. Валидация даты рождения - отклоняем мусор
        if data.dob and not self.validate_date(data.dob):
            if self.debug:
                print(f"❌ Дата рождения '{data.dob}' не прошла валидацию, сбрасываем")
            data.dob = ""

        # 10. Валидация срока действия - отклоняем мусор вроде EVA<<K
        if data.expiration_date and not self.validate_date(data.expiration_date):
            if self.debug:
                print(f"❌ Срок действия '{data.expiration_date}' не прошел валидацию, сбрасываем")
            data.expiration_date = ""

        if self.debug:
            print("\n📊 ИТОГОВЫЕ ДАННЫЕ:")
            print(f"   Фамилия: {data.last_name}")
            print(f"   Имя: {data.first_name}")
            print(f"   Документ: {data.document_number}")
            print(f"   ИИН: {data.iin}")
            print(f"   Дата рождения: {data.dob}")
            print(f"   Пол: {data.gender}")
            print(f"   Валидность: {data.is_valid}")
            print("="*60)

        return data


def test_easyocr_parser(file_path: str):
    """Тестирование парсера"""
    parser = PassportParserEasyOCR(debug=True)
    result = parser.parse(file_path)
    print("\n🎯 РЕЗУЛЬТАТ:")
    print(result.to_dict())
    return result

PassportParser = PassportParserEasyOCR
