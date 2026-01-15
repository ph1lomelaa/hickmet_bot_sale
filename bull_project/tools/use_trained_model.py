"""
Использование обученной ML модели для парсинга паспортов

Использование:
    from use_trained_model import PassportMLParser

    parser = PassportMLParser('passport_model/')
    result = parser.parse_text(ocr_text)
"""

from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PassportData:
    """Данные паспорта"""
    last_name: str = ""
    first_name: str = ""
    iin: str = ""
    document_number: str = ""
    date_of_birth: str = ""
    gender: str = ""
    confidence: float = 0.0


class PassportMLParser:
    """ML парсер для паспортов"""

    def __init__(self, model_path: str):
        """
        Args:
            model_path: Путь к обученной модели
        """
        print(f"📦 Загрузка модели из {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.model.eval()

        # Инвертируем label2id для получения имен меток
        self.id2label = self.model.config.id2label

        print("✅ Модель загружена")

    def parse_text(self, text: str) -> PassportData:
        """
        Парсинг OCR текста паспорта

        Args:
            text: OCR текст паспорта

        Returns:
            PassportData с извлеченными полями
        """
        # Токенизация
        tokens = text.split()
        inputs = self.tokenizer(
            tokens,
            is_split_into_words=True,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=512
        )

        # Предсказание
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)
            confidences = torch.softmax(outputs.logits, dim=2).max(dim=2).values

        # Декодирование предсказаний
        predicted_labels = [
            self.id2label[pred_id.item()]
            for pred_id in predictions[0]
        ]

        # Выравнивание меток с токенами
        word_ids = inputs.word_ids(batch_index=0)
        aligned_labels = []
        aligned_confidences = []

        for i, word_id in enumerate(word_ids):
            if word_id is not None:
                aligned_labels.append(predicted_labels[i])
                aligned_confidences.append(confidences[0][i].item())

        # Извлечение сущностей
        entities = self._extract_entities(tokens, aligned_labels, aligned_confidences)

        # Формирование результата
        data = PassportData(
            last_name=entities.get('SURNAME', ''),
            first_name=entities.get('FIRSTNAME', ''),
            iin=entities.get('IIN', ''),
            document_number=entities.get('DOC', ''),
            date_of_birth=entities.get('DOB', ''),
            confidence=self._calculate_confidence(entities, aligned_confidences)
        )

        # Определение пола по ИИН (если есть)
        if data.iin and len(data.iin) == 12:
            gender_digit = int(data.iin[6])
            data.gender = 'M' if gender_digit in [1, 3, 5] else 'F'

        return data

    def _extract_entities(self, tokens: List[str], labels: List[str],
                          confidences: List[float]) -> Dict[str, str]:
        """Извлечение сущностей из токенов и меток"""
        entities = {}
        current_entity = None
        current_tokens = []

        for token, label, conf in zip(tokens, labels, confidences):
            if label.startswith('B-'):
                # Начало новой сущности
                if current_entity and current_tokens:
                    entities[current_entity] = ' '.join(current_tokens)

                current_entity = label[2:]  # Убираем B-
                current_tokens = [token]

            elif label.startswith('I-') and current_entity == label[2:]:
                # Продолжение текущей сущности
                current_tokens.append(token)

            elif label == 'O':
                # Конец сущности
                if current_entity and current_tokens:
                    entities[current_entity] = ' '.join(current_tokens)
                current_entity = None
                current_tokens = []

        # Добавляем последнюю сущность
        if current_entity and current_tokens:
            entities[current_entity] = ' '.join(current_tokens)

        return entities

    def _calculate_confidence(self, entities: Dict[str, str],
                              confidences: List[float]) -> float:
        """Расчет общей уверенности в результате"""
        if not confidences:
            return 0.0

        # Средняя уверенность по всем токенам
        avg_confidence = sum(confidences) / len(confidences)

        # Штрафы за отсутствие критических полей
        penalty = 0.0
        if not entities.get('SURNAME'):
            penalty += 0.2
        if not entities.get('FIRSTNAME'):
            penalty += 0.2
        if not entities.get('IIN'):
            penalty += 0.15

        return max(0.0, avg_confidence - penalty)

    def parse_batch(self, texts: List[str]) -> List[PassportData]:
        """
        Пакетная обработка паспортов

        Args:
            texts: Список OCR текстов

        Returns:
            Список PassportData
        """
        return [self.parse_text(text) for text in texts]


# Пример использования
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Использование: python use_trained_model.py <model_path>")
        sys.exit(1)

    model_path = sys.argv[1]
    parser = PassportMLParser(model_path)

    # Тестовый текст
    test_text = """
    ПАСПОРТ / PASSPORT
    КОД ГОСУДАРСТВА / CODE OF STATE KAZ
    ФАМИЛИЯ / SURNAME GAJIYEV
    ИМЯ / GIVEN NAMES ASKER
    ИИН / IIN 800306302949
    НОМЕР / NUMBER N19640426
    ДАТА РОЖДЕНИЯ / DATE OF BIRTH 06.03.1980
    """

    print("\n📄 Тестовый текст:")
    print(test_text)

    result = parser.parse_text(test_text)

    print("\n✅ Результат парсинга:")
    print(f"   Фамилия: {result.last_name}")
    print(f"   Имя: {result.first_name}")
    print(f"   ИИН: {result.iin}")
    print(f"   Документ: {result.document_number}")
    print(f"   Дата рождения: {result.date_of_birth}")
    print(f"   Пол: {result.gender}")
    print(f"   Уверенность: {result.confidence:.2%}")
