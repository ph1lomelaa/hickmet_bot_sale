# 📋 Руководство по проверке паспортов

## ✅ Что было исправлено

### Проблема:
- ❌ При парсинге паспорта НЕ проверялся срок действия
- ❌ `passport_warning` не возвращался в некоторых API endpoints
- ❓ Нужно было убедиться что парсер не путает expiry date с date of issue

### Решение:
- ✅ Добавлена проверка срока паспорта при парсинге
- ✅ `passport_warning` теперь возвращается во ВСЕХ API endpoints
- ✅ Парсер ПРАВИЛЬНО различает expiry date и date of issue

---

## 🎯 Как работает проверка паспортов

### 1️⃣ Проверка срока действия

Функция `check_passport_expiry()` проверяет срок действия паспорта:

```python
def check_passport_expiry(passport_expiry: str) -> Optional[str]:
    """
    Проверяет срок действия паспорта.
    Если паспорт истекает в течение 6 месяцев - возвращает предупреждение.
    """
```

**Что проверяется:**
- ⚠️ Паспорт просрочен → "⚠️ ПАСПОРТ ПРОСРОЧЕН на X дн."
- ⚠️ Истекает в течение 6 месяцев → "⚠️ Истекает через X мес. (Y дн.)"
- ✅ Срок в порядке → None

**Поддерживаемые форматы дат:**
- `DD.MM.YYYY` (01.12.2030)
- `YYYY-MM-DD` (2030-12-01)
- `DD/MM/YYYY` (01/12/2030)

---

### 2️⃣ Парсинг паспортов

Парсер **НЕ ПУТАЕТ** expiry date с date of issue:

```python
# Ключевые слова для date of issue:
issue_patterns = [
    "DATE OF ISSUE", "DATEOFISSUE", "ISSUE DATE",
    "ISSUED ON", "ISSUED", "ДАТА ВЫДАЧИ"
]

# Ключевые слова для expiry date:
expiry_patterns = [
    "DATE OF EXPIRY", "DATEOFEXPIRY", "EXPIRY",
    "EXPIRES", "VALID UNTIL", "VALID THRU",
    "СРОК ДЕЙСТВИЯ", "ДЕЙСТВИТЕЛЕН ДО"
]
```

**Логика выбора expiry date:**
1. Ищет даты с контекстом "EXPIRY" → берет самую позднюю
2. Если не нашел → берет самую позднюю дату которая НЕ "ISSUE" и НЕ "BIRTH"
3. Игнорирует date of issue

---

### 3️⃣ Где проверяется срок действия

Проверка происходит в **4 местах:**

#### 1. При парсинге паспорта (`/api/passport/parse`)

```python
@app.post("/api/passport/parse")
async def api_passport_parse(file: UploadFile):
    passport_data = await passport_parser.parse(temp_path)

    # 🔥 Проверяем срок действия
    if passport_data.document_type == "id_card":
        passport_warning = "⚠️ Загружено удостоверение личности"
    else:
        passport_warning = check_passport_expiry(passport_data.expiration_date)

    result_data['passport_warning'] = passport_warning
```

**Когда срабатывает:**
- Менеджер загружает паспорт через WebApp
- Сразу видит предупреждение если срок истекает

---

#### 2. При создании брони (`/api/bookings/submit`)

```python
for pilgrim in payload.pilgrims:
    # Проверяем срок действия паспорта
    passport_warning = None
    if is_id_card:
        passport_warning = "⚠️ Загружено удостоверение личности"
    else:
        passport_warning = check_passport_expiry(pilgrim.passport_expiry)

    # Сохраняем в БД
    record_db["passport_warning"] = passport_warning
```

**Когда срабатывает:**
- Менеджер сабмитит бронь
- Предупреждение сохраняется в БД

---

#### 3. При обновлении брони (`PATCH /api/bookings/{booking_id}`)

```python
if p.passport_expiry:
    update_fields['passport_expiry'] = p.passport_expiry

    # 🔥 Проверяем срок действия при обновлении
    passport_warning = check_passport_expiry(p.passport_expiry)
    update_fields['passport_warning'] = passport_warning
```

**Когда срабатывает:**
- Менеджер обновляет данные брони
- Загружает новый паспорт

---

#### 4. При загрузке фото паспорта

```python
if p.passport_image_path:
    # Проверяем существующий срок действия в БД
    if booking.passport_expiry:
        passport_warning = check_passport_expiry(booking.passport_expiry)
        update_fields['passport_warning'] = passport_warning
```

**Когда срабатывает:**
- Менеджер загружает фото паспорта к существующей брони

---

### 4️⃣ Где возвращается `passport_warning`

`passport_warning` теперь возвращается во **ВСЕХ** API endpoints:

✅ `POST /api/passport/parse` - парсинг паспорта
✅ `GET /api/history/{manager_id}` - история менеджера
✅ `GET /api/admin/bookings` - все брони за период
✅ `GET /api/bookings/{booking_id}` - детали брони
✅ `GET /api/care/search` - поиск паломника

**Формат ответа:**

```json
{
  "ok": true,
  "data": {
    "guest_last_name": "Иванов",
    "guest_first_name": "Иван",
    "passport_expiry": "01.12.2025",
    "passport_warning": "⚠️ Истекает через 10 мес. (300 дн.)",
    ...
  }
}
```

---

## 🖥️ Как показывать предупреждения во frontend

### Пример 1: Список броней (history_v2.html)

```javascript
function renderBooking(booking) {
    let html = `
        <div class="booking-card">
            <div class="name">${booking.guest_last_name} ${booking.guest_first_name}</div>
    `;

    // 🔥 Показываем предупреждение о паспорте
    if (booking.passport_warning) {
        html += `
            <div class="warning" style="color: red; font-size: 12px; margin-top: 4px;">
                ${booking.passport_warning}
            </div>
        `;
    }

    html += `
            <div class="info">Пакет: ${booking.package_name}</div>
        </div>
    `;

    return html;
}
```

**Результат:**
```
┌────────────────────────────┐
│ Иванов Иван                │
│ ⚠️ Истекает через 4 мес.   │ ← КРАСНЫМ
│ Пакет: Умра 25-Янв         │
└────────────────────────────┘
```

---

### Пример 2: При загрузке паспорта (index.html)

```javascript
async function handlePassportUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/passport/parse', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();

    if (result.ok) {
        const data = result.data;

        // Заполняем поля
        document.getElementById('lastName').value = data.last_name;
        document.getElementById('firstName').value = data.first_name;

        // 🔥 Показываем предупреждение если есть
        if (data.passport_warning) {
            showWarning(data.passport_warning);
        }
    }
}

function showWarning(message) {
    const warningDiv = document.createElement('div');
    warningDiv.className = 'passport-warning';
    warningDiv.style.cssText = `
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        color: #856404;
        padding: 12px;
        margin: 10px 0;
        border-radius: 4px;
        font-size: 14px;
    `;
    warningDiv.textContent = message;

    // Вставляем под именем паломника
    const nameSection = document.querySelector('.pilgrim-name');
    nameSection.after(warningDiv);
}
```

**Результат:**
```
Фамилия: Иванов
Имя: Иван

╔══════════════════════════════════════╗
║ ⚠️ Истекает через 4 мес. (120 дн.)   ║ ← ЖЕЛТЫМ
╚══════════════════════════════════════╝

Дата рождения: 01.01.1990
...
```

---

### Пример 3: Поиск паломника (search-pilgrim.html)

```javascript
function renderSearchResults(results) {
    const container = document.getElementById('results');
    container.innerHTML = '';

    results.forEach(tourist => {
        const card = document.createElement('div');
        card.className = 'tourist-card';

        card.innerHTML = `
            <div class="tourist-name">
                ${tourist.last_name} ${tourist.first_name}
            </div>
        `;

        // 🔥 Предупреждение о паспорте
        if (tourist.passport_warning) {
            const warning = document.createElement('div');
            warning.className = 'passport-warning';
            warning.style.color = 'red';
            warning.style.fontSize = '12px';
            warning.style.marginTop = '4px';
            warning.textContent = tourist.passport_warning;
            card.appendChild(warning);
        }

        card.innerHTML += `
            <div>Паспорт: ${tourist.passport_num}</div>
            <div>Телефон: ${tourist.phone}</div>
        `;

        container.appendChild(card);
    });
}
```

---

## 📊 Типы предупреждений

### 1. Паспорт просрочен
```
⚠️ ПАСПОРТ ПРОСРОЧЕН на 45 дн.
```
- Цвет: **КРАСНЫЙ** (#dc3545)
- Действие: Обязательно обновить паспорт

### 2. Истекает скоро (< 6 месяцев)
```
⚠️ Истекает через 4 мес. (120 дн.)
```
- Цвет: **ОРАНЖЕВЫЙ** (#ffc107)
- Действие: Рекомендуется обновить

### 3. Удостоверение личности вместо паспорта
```
⚠️ Загружено удостоверение личности, требуется заграничный паспорт
```
- Цвет: **КРАСНЫЙ** (#dc3545)
- Действие: Загрузить заграничный паспорт

---

## 🧪 Тестирование

### Тест 1: Загрузить паспорт с истекшим сроком

1. Создать тестовый паспорт с датой expiry: `01.01.2024`
2. Загрузить через `/api/passport/parse`
3. Проверить ответ:
```json
{
  "ok": true,
  "data": {
    "passport_warning": "⚠️ ПАСПОРТ ПРОСРОЧЕН на X дн.",
    ...
  }
}
```

### Тест 2: Создать бронь

1. Создать бронь с паспортом истекающим через 3 месяца
2. Проверить что `passport_warning` сохранилось в БД
3. Получить бронь через `/api/history/{manager_id}`
4. Проверить что `passport_warning` возвращается

### Тест 3: Парсер не путает issue и expiry

1. Создать паспорт где:
   - Date of issue: `01.01.2020`
   - Date of expiry: `01.01.2030`
2. Загрузить через парсер
3. Проверить что `expiration_date` = `01.01.2030` (НЕ 2020!)

---

## ✅ Чек-лист проверки

### Backend (API):
- [x] `check_passport_expiry()` работает корректно
- [x] Проверка при парсинге паспорта
- [x] Проверка при создании брони
- [x] Проверка при обновлении брони
- [x] `passport_warning` возвращается во ВСЕХ endpoints
- [x] Парсер не путает expiry с issue

### Frontend (нужно проверить):
- [ ] Предупреждения показываются при загрузке паспорта
- [ ] Предупреждения показываются в списке броней
- [ ] Предупреждения показываются при поиске паломника
- [ ] Предупреждения показываются в карточке брони
- [ ] Правильные цвета (красный/оранжевый)
- [ ] Правильное расположение (под именем паломника)

---

## 📝 Рекомендации для frontend

### Где показывать предупреждения:

1. **При загрузке паспорта** - сразу под именем паломника
2. **В списке броней** - под именем в карточке
3. **При поиске** - в результатах поиска
4. **В деталях брони** - в информации о паломнике
5. **В истории** - в каждой записи

### Стили:

```css
.passport-warning {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 8px 12px;
    margin: 8px 0;
    font-size: 13px;
    color: #856404;
    border-radius: 4px;
}

.passport-warning.expired {
    background-color: #f8d7da;
    border-left-color: #dc3545;
    color: #721c24;
}
```

---

## 🎉 Итог

✅ **Проверка паспортов работает ВЕЗДЕ:**
- При парсинге
- При создании/обновлении
- Во всех API endpoints

✅ **Парсер правильно распознает:**
- Не путает expiry date с date of issue
- Поддерживает разные форматы дат
- Определяет ID card vs passport

✅ **Предупреждения подробные:**
- Показывают сколько осталось времени
- Разные типы предупреждений
- Готовы для отображения во frontend

**Осталось:** Добавить отображение предупреждений во frontend! 🚀
