import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from backend.core.config import settings
from backend.db.database import init_db
from backend.api.v1 import auth, complaints, users, employees, websocket

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(settings.LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Backend API...")
    await init_db()
    if settings.SSL_CERT_PATH:
        logger.info(f"✅ HTTPS API запущен на https://{settings.DOMAIN}:{settings.API_HTTPS_PORT}")
    else:
        logger.info(f"✅ API запущен на http://{settings.API_HOST}:{settings.API_PORT}")
    yield
    logger.info("🛑 Остановка Backend...")

app = FastAPI(
    title="Городской помощник API",
    description="Backend для Telegram бота и Web Apps",
    version="0.7.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["complaints"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(employees.router, prefix="/api/v1/employees", tags=["employees"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["websocket"])

# Статические файлы для Mini Apps
try:
    from fastapi.staticfiles import StaticFiles
    app.mount("/webapp/residents", StaticFiles(directory="frontend/residents", html=True), name="residents")
    app.mount("/webapp/services", StaticFiles(directory="frontend/services", html=True), name="services")
except Exception as e:
    logger.warning(f"⚠️  Не удалось подключить статические файлы: {e}")

@app.get("/")
async def root():
    return {"name": "Городской помощник API", "version": "0.7.1", "status": "running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    if settings.SSL_CERT_PATH and settings.SSL_KEY_PATH:
        uvicorn.run(
            "backend.main:app",
            host=settings.API_HOST,
            port=settings.API_HTTPS_PORT,
            ssl_certfile=settings.SSL_CERT_PATH,
            ssl_keyfile=settings.SSL_KEY_PATH,
            reload=False,
            log_level=settings.LOG_LEVEL.lower()
        )
    else:
        uvicorn.run(
            "backend.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=False,
            log_level=settings.LOG_LEVEL.lower()
        )
