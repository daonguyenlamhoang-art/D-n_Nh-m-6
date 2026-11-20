"""Điểm khởi động của NightFood Backend.

Chạy:  uvicorn app.main:app --reload
Tài liệu API tự sinh: http://127.0.0.1:8000/docs
"""
import os
import sys

# Đảm bảo UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app import models  # noqa: F401 - import để SQLAlchemy biết các bảng
from app.core.config import settings
from app.db.session import Base, engine
from app.routers import admin, categories, dishes, health, items, orders, store


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print(f"[DB] Connected to MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    except OperationalError as error:
        print(f"[DB] Cannot connect to MySQL: {error.orig}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Hệ thống API quán bán đồ ăn đêm trực tuyến NightFood (SRS v1.2)",
    version="1.2.0",
    lifespan=lifespan,
)

# CORS: cho phép Frontend gọi được API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Bắt và định dạng lỗi chuẩn hóa theo mục 8.1 SRS: {"error": {"code": "...", "message": "...", "details": {}}}
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {},
            }
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_err = exc.errors()[0] if exc.errors() else {}
    msg = first_err.get("msg", "Dữ liệu không hợp lệ")
    field = ".".join(str(x) for x in first_err.get("loc", []))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Lỗi nhập liệu tại trường '{field}': {msg}",
                "details": exc.errors(),
            }
        },
    )


# Đăng ký các router tiền tố /api
app.include_router(health.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(store.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(dishes.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


# Phục vụ Frontend tĩnh trực tiếp từ FastAPI (Chương 10 SRS: tránh CORS và bảo đảm cookie session mượt mà)
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/api")
def api_root():
    return {
        "app": settings.APP_NAME,
        "version": "1.2.0",
        "docs_url": "/docs",
        "description": "Website bán đồ ăn đêm trực tuyến NightFood",
    }
