FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY bull_project/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY bull_project /app/bull_project

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /home/appuser/.EasyOCR \
    && chown -R appuser:appuser /app /home/appuser

USER appuser
ENV HOME=/home/appuser

RUN python - <<'PY'
import easyocr
print("Preloading EasyOCR models (en, ru)...")
easyocr.Reader(['en', 'ru'], gpu=False)
print("EasyOCR models ready.")
PY

EXPOSE 8000

CMD ["uvicorn", "bull_project.bull_bot.core.api_server:app", "--host", "0.0.0.0", "--port", "8000"]