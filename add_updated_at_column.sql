-- Добавление колонки updated_at в таблицу bookings
-- Эту миграцию нужно выполнить на продакшене

ALTER TABLE bookings
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Инициализируем updated_at текущим значением created_at для существующих записей
UPDATE bookings SET updated_at = created_at WHERE updated_at IS NULL;

-- Для отмененных броней ставим updated_at = now() чтобы они показывались сверху
UPDATE bookings
SET updated_at = NOW()
WHERE status LIKE '%cancel%' OR status LIKE '%reschedule%';
