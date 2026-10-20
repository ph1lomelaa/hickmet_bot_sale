import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from bull_project.bull_bot.config.constants import ABS_UPLOADS_DIR
from bull_project.bull_bot.database.setup import init_db
from bull_project.bull_bot.api.access import api_access_guard, router as access_router
from bull_project.bull_bot.api.routes.rooms import router as rooms_router
from bull_project.bull_bot.api.routes.admin_requests import router as admin_requests_router
from bull_project.bull_bot.api.routes.open_date import router as open_date_router
from bull_project.bull_bot.api.routes.websockets import router as websockets_router
from bull_project.bull_bot.api.routes.packages import router as packages_router
from bull_project.bull_bot.api.routes.bookings import router as bookings_router
from bull_project.bull_bot.api.routes.care import router as care_router
from bull_project.bull_bot.api.routes.passports import router as passports_router
from bull_project.bull_bot.api.routes.admin import router as admin_router

os.makedirs(ABS_UPLOADS_DIR, exist_ok=True)
app = FastAPI()
app.middleware("http")(api_access_guard)
app.include_router(access_router)

# ──────────────────────────────────────────────────────────────────────────
# Защита от сканеров/ботов: блокировка обхода пути + rate limiting.
# Работает на входе для ВСЕХ эндпоинтов (до роутинга), без внешних зависимостей.
# Параметры можно переопределить через переменные окружения.
# ──────────────────────────────────────────────────────────────────────────
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))     # окно, сек
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "240"))          # запросов/окно с одного IP
SCANNER_BLOCK_SECONDS = int(os.getenv("SCANNER_BLOCK_SECONDS", "900"))  # бан скана, сек

# Маркеры явного сканирования (path traversal / попытки читать секреты).
# Проверяются как подстроки в пути — легитимные запросы их не содержат.
_SCANNER_MARKERS = (
    "..", "\x00", "\\",
    "/etc/", "/proc/", "/root/", "/sys/", "/var/",
    ".ssh", "id_rsa", "id_ed25519", ".git-credentials", ".git/config",
    ".aws", ".env", ".credentials", "auth.json", "hosts.yml",
    "/passwd", "/shadow", ".npmrc", ".docker",
)

_rate_hits: dict[str, deque] = defaultdict(deque)  # ip -> времена запросов
_blocked_ips: dict[str, float] = {}                # ip -> время разбана
_last_prune = 0.0


def _client_ip(request: Request) -> str:
    # За реверс-прокси (Caddy) реальный IP — в X-Forwarded-For
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _prune(now: float) -> None:
    for ip in list(_rate_hits.keys()):
        dq = _rate_hits[ip]
        while dq and now - dq[0] > RATE_LIMIT_WINDOW:
            dq.popleft()
        if not dq:
            del _rate_hits[ip]
    for ip in list(_blocked_ips.keys()):
        if now >= _blocked_ips[ip]:
            del _blocked_ips[ip]


async def security_guard(request: Request, call_next):
    global _last_prune
    now = time.time()
    ip = _client_ip(request)

    # периодическая чистка словарей, чтобы память не росла
    if now - _last_prune > RATE_LIMIT_WINDOW:
        _prune(now)
        _last_prune = now

    # 1) IP уже забанен за скан
    unblock = _blocked_ips.get(ip)
    if unblock is not None:
        if now < unblock:
            return PlainTextResponse("Forbidden", status_code=403)
        del _blocked_ips[ip]

    # 2) явная попытка обхода пути / чтения секретов → мгновенный бан
    path = request.url.path.lower()
    if any(marker in path for marker in _SCANNER_MARKERS):
        _blocked_ips[ip] = now + SCANNER_BLOCK_SECONDS
        return PlainTextResponse("Forbidden", status_code=403)

    # 3) rate limiting по IP (скользящее окно)
    dq = _rate_hits[ip]
    while dq and now - dq[0] > RATE_LIMIT_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT_MAX:
        return PlainTextResponse("Too Many Requests", status_code=429)
    dq.append(now)

    return await call_next(request)

app.middleware("http")(security_guard)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

app.include_router(rooms_router)
app.include_router(admin_requests_router)
app.include_router(open_date_router)
app.include_router(websockets_router)
app.include_router(packages_router)
app.include_router(bookings_router)
app.include_router(care_router)
app.include_router(passports_router)
app.include_router(admin_router)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARE_WEBAPP_DIR = os.path.join(PROJECT_ROOT, "care_webapp")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

@app.on_event("startup")
async def startup_event():
    from bull_project.bull_bot.core.access import validate_access_config
    validate_access_config()
    await init_db()

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


@app.get("/")
async def root():
    index_path = os.path.join(CARE_WEBAPP_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Bull API", "status": "running"}


def _safe_static_path(base_dir: str, rel_path: str):
    """Безопасно соединяет base_dir и относительный путь из URL.
    Возвращает абсолютный путь ТОЛЬКО если он реально лежит внутри base_dir,
    иначе None. Блокирует обход каталога (../../etc/passwd и т.п.)."""
    base = os.path.realpath(base_dir)
    # Абсолютные пути и обратные слэши недопустимы
    if not rel_path or rel_path.startswith(("/", "\\")) or "\x00" in rel_path:
        return None
    target = os.path.realpath(os.path.join(base, rel_path))
    if target == base or target.startswith(base + os.sep):
        return target
    return None


@app.get("/{full_path:path}")
async def catch_all(full_path: str):

    if full_path.startswith("api/"):
        return {"error": "API endpoint not found"}

    file_path = _safe_static_path(CARE_WEBAPP_DIR, full_path)
    if file_path and os.path.isfile(file_path):
        return FileResponse(file_path)

    asset_path = _safe_static_path(ASSETS_DIR, full_path)
    if asset_path and os.path.isfile(asset_path):
        return FileResponse(asset_path)

    # SPA-фолбэк: любой неизвестный путь отдаёт index.html (а не файлы ФС)
    index_path = os.path.join(CARE_WEBAPP_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"error": "Not found"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT") or os.getenv("PORT0") or "8000")
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
    )
