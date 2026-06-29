import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.account_routes import router as account_router
from app.api.routes import get_providers, router
from app.config import settings
from app.services.updater import run_daily_update

# 让应用与 APScheduler 的 INFO 日志可见（盘后更新进度、调度启动等）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def _scheduled_update() -> None:
    await run_daily_update(get_providers(), date.today())


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    scheduler: AsyncIOScheduler | None = None
    if settings.scheduler_enabled:
        scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        scheduler.add_job(
            _scheduled_update,
            CronTrigger(hour=settings.update_hour, minute=settings.update_minute),
        )
        scheduler.start()
        logger.info(
            "盘后更新调度已启动：每日 %02d:%02d %s",
            settings.update_hour,
            settings.update_minute,
            settings.scheduler_timezone,
        )
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(title="acquisition", version="0.1.0", lifespan=lifespan)

# 前端(EdgeOne, stocks.marsian.cn) 与后端(api.stocks.marsian.cn) 不同源，需放行 CORS。
# JWT 走 Authorization 头、不用 cookie，故 allow_credentials=False。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(account_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
