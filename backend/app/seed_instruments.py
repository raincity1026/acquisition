"""一次性初始化：拉全市场 A 股标的列表灌进 instruments 表。

这是**搜索 / 自选的数据基础**（设计规格 M3 §2）。行情按需抓取，但标的列表要全量预加载。
幂等，可重复跑。也顺带验证本机能否访问数据源（拉到几千条即说明连通）。

用法（本地）:        uv run python -m app.seed_instruments
用法（生产容器内）:  docker compose --env-file .env.prod -f docker-compose.prod.yml \
                        exec backend uv run python -m app.seed_instruments
"""

import asyncio
import logging

from app.providers.akshare_provider import AkshareProvider
from app.providers.baostock_provider import BaostockProvider
from app.services.market_data import _AllProvidersFailed, _with_fallback
from app.storage import repository as repo
from app.storage.database import SessionMaker, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
logger = logging.getLogger(__name__)


async def seed() -> int:
    # 主源 Baostock（含指数），失败降级 AKShare(sina，仅股票)
    providers = [BaostockProvider(), AkshareProvider()]
    try:
        items = await _with_fallback(providers, lambda p: p.list_instruments())
    except _AllProvidersFailed:
        logger.error("所有数据源都拉取标的列表失败——请确认本机能访问 baostock / akshare")
        return 0
    async with SessionMaker() as session:
        await repo.upsert_instruments(session, items)
        total = await repo.count_instruments(session)
    logger.info("已导入标的 %d 条；库内现有 %d 条", len(items), total)
    await engine.dispose()
    return total


if __name__ == "__main__":
    asyncio.run(seed())
