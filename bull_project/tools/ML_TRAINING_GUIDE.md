# 🤖 Руководство по обучению ML модели для парсинга паспортов

## 📋 Что нужно для обучения

### 1. Размеченные данные

| Количество | Качество модели | Время разметки |
|------------|----------------|----------------|
| 200-500 паспортов | Базовое (85-90%) | ~10-25 часов |
| 500-1000 паспортов | Хорошее (90-95%) | ~25-50 часов |
| 1000-2000 паспортов | Отличное (95-98%) | ~50-100 часов |
| 5000+ паспортов | Превосходное (98-99%) | ~250+ часов |

**💡 Совет:** Начните с 300-500 паспортов для первой версии модели.

### 2. Оборудование

**Опция A: Локальный компьютер**
```
✅ GPU: NVIDIA RTX 3060+ (8GB VRAM)
✅ RAM: 16GB+
✅ Место: 50GB свободно
✅ ОС: Windows/Linux/Mac
```

**Опция B: Облако (рекомендуется)**
```
✅ Google Colab (бесплатно): T4 GPU, 12GB VRAM
✅ Kaggle (бесплатно): P100 GPU, 16GB VRAM
✅ AWS EC2 (платно): от $0.50/час
```

### 3. Программное обеспечение

```bash
# Python 3.8+
pip install transformers==4.35.0
pip install datasets==2.14.0
pip install torch==2.1.0
pip install scikit-learn==1.3.0
```

## 🚀 Пошаговая инструкция

### Шаг 1: Разметка данных (10-50 часов)

1. Откройте `passport_annotator.html` в браузере
2. Загрузите OCR текст паспорта
3. Заполните поля (фамилия, имя, ИИН и т.д.)
4. Нажмите "Сохранить"
5. Повторите для 300-500 паспортов
6. Нажмите "Скачать датасет" → получите `passport_dataset.json`

**Пример размеченных данных:**
```json
[
  {
    "file": "passport_001.pdf",
    "ocr_text": "ПАСПОРТ SURNAME GAJIYEV GIVEN NAMES ASKER ИИН 800306302949",
    "labels": {
      "last_name": "GAJIYEV",
      "first_name": "ASKER",
      "iin": "800306302949",
      "document_number": "N19640426",
      "date_of_birth": "06.03.1980",
      "gender": "M"
    }
  }
]
```

### Шаг 2: Обучение модели (1-3 часа)

#### Локально:
```bash
cd /Users/muslimakosmagambetova/Downloads/tired2\ 2/bull_project/tools

python train_passport_model.py \
  --dataset passport_dataset.json \
  --output ../models/passport_model \
  --epochs 3 \
  --batch-size 16
```

#### В Google Colab:
1. Загрузите файлы в Google Drive
2. Откройте [Google Colab](https://colab.research.google.com/)
3. Создайте новый notebook
4. Выполните:

```python
# Подключение к Drive
from google.colab import drive
drive.mount('/content/drive')

# Установка зависимостей
!pip install transformers datasets torch

# Копирование скриптов
!cp /content/drive/MyDrive/train_passport_model.py .
!cp /content/drive/MyDrive/passport_dataset.json .

# Обучение
!python train_passport_model.py \
  --dataset passport_dataset.json \
  --output passport_model/ \
  --epochs 3 \
  --batch-size 16
```

### Шаг 3: Тестирование модели (10 минут)

```bash
python use_trained_model.py ../models/passport_model
```

Или в коде:
```python
from use_trained_model import PassportMLParser

parser = PassportMLParser('../models/passport_model')

ocr_text = """
ПАСПОРТ / PASSPORT
SURNAME GAJIYEV
GIVEN NAMES ASKER
ИИН 800306302949
"""

result = parser.parse_text(ocr_text)
print(f"Фамилия: {result.last_name}")
print(f"Имя: {result.first_name}")
print(f"Confidence: {result.confidence:.2%}")
```

### Шаг 4: Интеграция в парсер

Добавьте ML fallback в текущий парсер:

```python
# В passport_parser.py
from tools.use_trained_model import PassportMLParser

class PassportParserEasyOCR:
    def __init__(self, use_ml_fallback=True):
        # ... существующий код ...

        # Добавляем ML fallback
        self.use_ml_fallback = use_ml_fallback
        if use_ml_fallback:
            try:
                from tools.use_trained_model import PassportMLParser
                self.ml_parser = PassportMLParser('../models/passport_model')
                print("✅ ML fallback загружен")
            except Exception as e:
                print(f"⚠️ ML fallback недоступен: {e}")
                self.ml_parser = None

    def parse(self, file_path: str) -> PassportData:
        # 1. Попытка regex парсинга
        data = self._parse_with_regex(file_path)

        # 2. Проверка уверенности
        confidence = self._calculate_confidence(data)

        # 3. Если уверенность низкая - пробуем ML
        if confidence < 0.85 and self.ml_parser:
            if self.debug:
                print(f"⚠️ Regex confidence={confidence:.2f}, trying ML...")

            ocr_text = self.extract_text_easyocr(file_path)
            ml_data = self.ml_parser.parse_text(ocr_text)

            # Используем ML результат если он лучше
            if ml_data.confidence > confidence:
                data = ml_data
                if self.debug:
                    print(f"✅ ML confidence={ml_data.confidence:.2f}, using ML result")

        return data
```

## 📊 Мониторинг качества

### Метрики для отслеживания:

1. **Accuracy** - процент правильно распознанных полей
2. **F1-Score** - баланс precision/recall
3. **Confidence** - средняя уверенность модели
4. **Rejection Rate** - процент отправленных на ручную проверку

### Тестирование:

```python
# test_model.py
from use_trained_model import PassportMLParser
import json

parser = PassportMLParser('passport_model/')

# Загружаем тестовый датасет
with open('test_dataset.json') as f:
    test_data = json.load(f)

correct = 0
total = 0

for item in test_data:
    result = parser.parse_text(item['ocr_text'])
    labels = item['labels']

    # Проверяем фамилию
    if result.last_name == labels['last_name']:
        correct += 1
    total += 1

    # Проверяем имя
    if result.first_name == labels['first_name']:
        correct += 1
    total += 1

accuracy = correct / total
print(f"Accuracy: {accuracy:.2%}")
```

## 💰 Стоимость обучения

| Платформа | Стоимость | Время обучения |
|-----------|-----------|----------------|
| Google Colab (Free) | $0 | 1-2 часа |
| Kaggle (Free) | $0 | 1-2 часа |
| AWS EC2 (g4dn.xlarge) | ~$1 | 1-2 часа |
| Google Cloud (n1-standard-4 + T4) | ~$1.50 | 1-2 часа |

**Для 1000 паспортов:**
- Разметка (50 часов * $10/час): $500
- Обучение: $0-2
- **Итого: ~$500 (в основном труд)**

## 🔄 Улучшение модели

### Когда переобучать:

1. Появились новые форматы паспортов (другие страны)
2. Точность упала ниже 90%
3. Добавлено 500+ новых размеченных паспортов
4. Изменились требования (новые поля)

### Активное обучение:

```python
# Собираем паспорты с низкой уверенностью
low_confidence = []

for passport_file in passport_files:
    result = parser.parse(passport_file)
    if result.confidence < 0.80:
        low_confidence.append({
            'file': passport_file,
            'result': result,
            'needs_review': True
        })

# Отправляем на ручную проверку
# После проверки добавляем в датасет и переобучаем
```

## 🎯 Следующие шаги

1. ✅ Разметьте 300 паспортов (начните с простых)
2. ✅ Обучите первую версию модели
3. ✅ Протестируйте на 50 новых паспортах
4. ✅ Соберите feedback и улучшите разметку
5. ✅ Разметьте еще 200 паспортов
6. ✅ Переобучите с полным датасетом (500)
7. ✅ Интегрируйте в production

## 🆘 Помощь

### Частые ошибки:

**"CUDA out of memory"**
- Уменьшите batch_size до 8 или 4
- Используйте gradient_checkpointing
- Переключитесь на distilbert (меньше модель)

**"Точность низкая (<85%)"**
- Проверьте качество разметки
- Добавьте больше данных
- Увеличьте epochs до 5-7
- Попробуйте bert-base вместо distilbert

**"Модель не обучается (loss не падает)"**
- Уменьшите learning rate
- Проверьте формат данных
- Увеличьте warmup_steps

## 📚 Дополнительные ресурсы

- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [Named Entity Recognition Tutorial](https://huggingface.co/learn/nlp-course/chapter7/2)
- [Fine-tuning BERT](https://mccormickml.com/2019/07/22/BERT-fine-tuning/)

---

**Вопросы?** Создайте issue в репозитории или напишите в Telegram.
