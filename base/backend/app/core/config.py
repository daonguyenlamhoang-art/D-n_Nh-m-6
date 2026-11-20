"""Đọc cấu hình từ file .env (hoặc biến môi trường)."""
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "NightFood"

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "food_night_db"

    # CORS
    CORS_ORIGINS: str = "*"

    # Giờ mở cửa quán ăn đêm (18h tối đến 2h sáng hôm sau)
    STORE_OPEN_HOUR: int = 18
    STORE_CLOSE_HOUR: int = 2
    # Cờ cho phép ép mở cửa phục vụ kiểm thử / demo vào ban ngày
    STORE_FORCE_OPEN: bool = True

    # Quản lý phiên
    SECRET_KEY: str = "nightfood-secret-key-super-secure-jwt-session-2026"
    SESSION_EXPIRE_HOURS: int = 8

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
