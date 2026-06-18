from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://acquisition:acquisition@localhost:5433/acquisition"

    # JWT。生产务必用环境变量覆盖 jwt_secret。
    jwt_secret: str = "dev-insecure-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 天

    # 盘后定时更新（默认关；生产 compose 用 SCHEDULER_ENABLED=true 开启）
    scheduler_enabled: bool = False
    update_hour: int = 18  # A股收盘后、数据源傍晚更全
    update_minute: int = 30
    scheduler_timezone: str = "Asia/Shanghai"


settings = Settings()
