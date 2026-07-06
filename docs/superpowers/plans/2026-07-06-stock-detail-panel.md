# 单股详情面板 + 框架结构调整 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把右主区做成个股详情页（报价摘要 + 基本面 + K 线），并把搜索框移到导航栏最左、去掉标题。

**Architecture:** 后端新增 `GET /api/instrument/{symbol}`，name/market/type/上市日读 DB，PE/PB/行业由 Baostock、市值由 AKShare 备源，服务层按字段合并（主源优先）。前端新增 `StockDetail.vue`（纯展示）+ `useInstrument`（取详情）+ `deriveQuote` 纯函数（从已取 K 线派生报价），在 `MarketView` 单股态编排，对比态不变。

**Tech Stack:** 后端 FastAPI + SQLAlchemy(async) + Baostock/AKShare，pytest/ruff/mypy(strict)；前端 Vue 3 + PrimeVue 4 + Vite，新增 vitest（仅测纯函数）。

## Global Constraints

- 内部 symbol 格式 `{code}.{market}`（如 `600519.SH`）；数据源转换一律走 `app.symbols`。
- Baostock 代码 `sh.600519`；AKShare 纯 `600519` 或 `sh600519`（按接口）。
- 触网的 provider 测试标记 `@pytest.mark.integration`（`pytest -m "not integration"` 可跳过）。
- 基本面任一字段取不到返回 `null`，不使请求失败；前端显示「—」。
- commit message 用英文。质量门禁：`uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -m "not integration"`。
- 后端命令在 `backend/` 下用 `uv run ...`；前端命令在 `frontend/` 下用 `npm`。

---

## 文件结构

**后端**
- Modify `backend/app/providers/base.py` — 加 `InstrumentDetail` 数据类 + `DataProvider.get_instrument_detail` 默认实现。
- Modify `backend/app/providers/baostock_provider.py` — 实现 `get_instrument_detail`（行业 + PE/PB）。
- Modify `backend/app/providers/akshare_provider.py` — 实现 `get_instrument_detail`（市值）。
- Modify `backend/app/services/market_data.py` — 加 `InstrumentDetailResult` + `get_instrument_detail`（合并）。
- Modify `backend/app/api/routes.py` — 加 `InstrumentDetailOut` + `GET /api/instrument/{symbol}`。
- Test `backend/tests/test_instrument_detail.py`（服务层，假 provider，非触网）。

**前端**
- Create `frontend/src/api/instrument.ts`
- Create `frontend/src/composables/useInstrument.ts`
- Create `frontend/src/utils/quote.ts` + `frontend/src/utils/quote.test.ts`
- Create `frontend/src/components/StockDetail.vue`
- Modify `frontend/src/views/MarketView.vue`（单股态插入详情）
- Modify `frontend/src/views/HomeView.vue`（导航栏）
- Modify `frontend/vite.config.ts`（vitest test 块）
- Modify `frontend/package.json`（vitest devDep + `test` script）

---

## Task 1: 后端 — InstrumentDetail 类型 + provider 基类默认实现

**Files:**
- Modify: `backend/app/providers/base.py`

**Interfaces:**
- Produces: `InstrumentDetail(industry, pe_ttm, pb_mrq, total_mv, circ_mv)`（全部可选，默认 None）；`DataProvider.get_instrument_detail(symbol) -> InstrumentDetail | None`（默认返回 None）。

- [ ] **Step 1: 在 base.py 加数据类**（放在 `Instrument` 之后）

```python
@dataclass(frozen=True)
class InstrumentDetail:
    """个股低频信息（不含逐日行情）。各源只填自己能取到的字段，缺失留 None。"""

    industry: str | None = None
    pe_ttm: float | None = None
    pb_mrq: float | None = None
    total_mv: float | None = None  # 总市值(元)
    circ_mv: float | None = None  # 流通市值(元)
```

- [ ] **Step 2: 在 `DataProvider` 里加带默认实现的方法**（非 abstract，放在 `get_trade_calendar` 抽象方法之后）

```python
    def get_instrument_detail(self, symbol: str) -> InstrumentDetail | None:
        """低频基本面；不支持的源返回 None（默认）。"""
        return None
```

- [ ] **Step 3: 门禁**

Run: `cd backend && uv run ruff check app/providers/base.py && uv run mypy app`
Expected: PASS（无错误）

- [ ] **Step 4: Commit**

```bash
git add backend/app/providers/base.py
git commit -m "feat(providers): add InstrumentDetail type and default get_instrument_detail"
```

---

## Task 2: 后端服务层 — get_instrument_detail（合并 + 单测）

**Files:**
- Modify: `backend/app/services/market_data.py`
- Test: `backend/tests/test_instrument_detail.py`

**Interfaces:**
- Consumes: `InstrumentDetail`（Task 1）、`repo.get_instrument`、`_ensure_instrument`、`UnknownSymbol`。
- Produces: `InstrumentDetailResult(symbol,name,market,type,ipo_date,industry,pe_ttm,pb_mrq,total_mv,circ_mv)`；`async get_instrument_detail(session, providers, symbol) -> InstrumentDetailResult`。

- [ ] **Step 1: 写失败测试** `backend/tests/test_instrument_detail.py`

```python
import pytest

from app.providers.base import Bar, DataProvider, Instrument, InstrumentDetail
from app.services import market_data as md
from app.services.market_data import UnknownSymbol, get_instrument_detail


class _Fake(DataProvider):
    def __init__(self, detail: InstrumentDetail | None) -> None:
        self._detail = detail

    def get_daily_bars(self, symbol, start, end):  # type: ignore[override]
        return []

    def list_instruments(self):  # type: ignore[override]
        return []

    def get_trade_calendar(self, start, end):  # type: ignore[override]
        return []

    def get_instrument_detail(self, symbol):  # type: ignore[override]
        return self._detail


@pytest.fixture
def patch_instrument(monkeypatch):
    from datetime import date

    inst = Instrument(
        symbol="600519.SH", name="贵州茅台", market="SH", type="stock",
        ipo_date=date(2001, 8, 27), status="listing",
    )

    async def _ensure(session, providers, symbol):
        if symbol != "600519.SH":
            raise UnknownSymbol(symbol)

    async def _get(session, symbol):
        return inst if symbol == "600519.SH" else None

    monkeypatch.setattr(md, "_ensure_instrument", _ensure)
    monkeypatch.setattr(md.repo, "get_instrument", _get)
    return inst


@pytest.mark.asyncio
async def test_merge_primary_wins_and_backup_fills(patch_instrument):
    primary = _Fake(InstrumentDetail(industry="白酒", pe_ttm=32.5, pb_mrq=9.8))
    backup = _Fake(InstrumentDetail(industry="酒", total_mv=1.98e12, circ_mv=1.98e12))
    r = await get_instrument_detail(None, [primary, backup], "600519.SH")
    assert r.name == "贵州茅台"
    assert r.industry == "白酒"  # 主源优先
    assert r.pe_ttm == 32.5
    assert r.total_mv == 1.98e12  # 备源补


@pytest.mark.asyncio
async def test_source_exception_is_not_fatal(patch_instrument):
    class _Boom(_Fake):
        def get_instrument_detail(self, symbol):
            raise RuntimeError("boom")

    r = await get_instrument_detail(None, [_Boom(None), _Fake(InstrumentDetail(pe_ttm=10.0))], "600519.SH")
    assert r.pe_ttm == 10.0


@pytest.mark.asyncio
async def test_unknown_symbol_raises(patch_instrument):
    with pytest.raises(UnknownSymbol):
        await get_instrument_detail(None, [_Fake(None)], "000000.SH")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/test_instrument_detail.py -v`
Expected: FAIL（`ImportError: cannot import name 'get_instrument_detail'`）

- [ ] **Step 3: 实现**（在 `market_data.py` 末尾追加）

```python
@dataclass
class InstrumentDetailResult:
    symbol: str
    name: str
    market: str
    type: str
    ipo_date: date | None
    industry: str | None
    pe_ttm: float | None
    pb_mrq: float | None
    total_mv: float | None
    circ_mv: float | None


def _merge_detail(base: InstrumentDetail, extra: InstrumentDetail) -> InstrumentDetail:
    """缺失字段用 extra 补（base 已有的不覆盖 → 主源优先）。"""
    return InstrumentDetail(
        industry=base.industry if base.industry is not None else extra.industry,
        pe_ttm=base.pe_ttm if base.pe_ttm is not None else extra.pe_ttm,
        pb_mrq=base.pb_mrq if base.pb_mrq is not None else extra.pb_mrq,
        total_mv=base.total_mv if base.total_mv is not None else extra.total_mv,
        circ_mv=base.circ_mv if base.circ_mv is not None else extra.circ_mv,
    )


async def get_instrument_detail(
    session: AsyncSession,
    providers: Sequence[DataProvider],
    symbol: str,
) -> InstrumentDetailResult:
    """详情：DB 取静态信息，逐源取基本面并按字段合并（主源优先，单源异常不致命）。"""
    await _ensure_instrument(session, providers, symbol)
    inst = await repo.get_instrument(session, symbol)
    assert inst is not None  # _ensure_instrument 已保证存在

    merged = InstrumentDetail()
    for p in providers:
        try:
            d = await asyncio.to_thread(p.get_instrument_detail, symbol)
        except Exception as e:  # noqa: BLE001 — 单源基本面失败不应致命
            logger.warning("provider %s 详情失败，跳过: %s", type(p).__name__, e)
            continue
        if d is not None:
            merged = _merge_detail(merged, d)

    return InstrumentDetailResult(
        symbol=symbol,
        name=inst.name,
        market=inst.market,
        type=inst.type,
        ipo_date=inst.ipo_date,
        industry=merged.industry,
        pe_ttm=merged.pe_ttm,
        pb_mrq=merged.pb_mrq,
        total_mv=merged.total_mv,
        circ_mv=merged.circ_mv,
    )
```

同时把 import 里的 `InstrumentDetail` 补上：将 `from app.providers.base import Bar, DataProvider, Instrument` 改为
`from app.providers.base import Bar, DataProvider, Instrument, InstrumentDetail`。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/test_instrument_detail.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 门禁 + Commit**

```bash
cd backend && uv run ruff check . && uv run ruff format . && uv run mypy app
git add backend/app/services/market_data.py backend/tests/test_instrument_detail.py
git commit -m "feat(service): merge instrument detail across providers (primary-first)"
```

---

## Task 3: 后端 Baostock — get_instrument_detail（行业 + PE/PB）

**Files:**
- Modify: `backend/app/providers/baostock_provider.py`

**Interfaces:**
- Produces: `BaostockProvider.get_instrument_detail(symbol) -> InstrumentDetail`（industry/pe_ttm/pb_mrq，市值留 None）。

- [ ] **Step 1: 补 import**

顶部 `from datetime import date` 改为 `from datetime import date, timedelta`；
`from .base import Bar, DataProvider, Instrument` 改为 `from .base import Bar, DataProvider, Instrument, InstrumentDetail`。

- [ ] **Step 2: 加方法**（`BaostockProvider` 类内，`list_instruments` 之后）

```python
    def get_instrument_detail(self, symbol: str) -> InstrumentDetail:
        code = to_baostock(symbol)

        def _fetch() -> tuple[list[list[str]], list[list[str]]]:
            with _session():
                ind = _rows(bs.query_stock_industry(code=code))
                end = date.today()
                start = end - timedelta(days=15)  # 近 15 天足够含最近交易日
                val = _rows(
                    bs.query_history_k_data_plus(
                        code, "date,peTTM,pbMRQ",
                        start_date=start.isoformat(), end_date=end.isoformat(),
                        frequency="d", adjustflag="3",
                    )
                )
            return ind, val

        ind, val = _retry(_fetch)
        # query_stock_industry 列: updateDate, code, code_name, industry, industryClassification
        industry = ind[0][3].strip() or None if ind and len(ind[0]) > 3 else None

        pe = pb = None
        for row in reversed(val):  # 取最近一个有值的交易日
            pe_s, pb_s = row[1].strip(), row[2].strip()
            if pe_s or pb_s:
                pe = float(pe_s) if pe_s else None
                pb = float(pb_s) if pb_s else None
                break

        return InstrumentDetail(industry=industry, pe_ttm=pe, pb_mrq=pb)
```

- [ ] **Step 3: 触网冒烟测试**（可选但推荐；标记 integration）`backend/tests/test_baostock_detail_integration.py`

```python
import pytest

from app.providers.baostock_provider import BaostockProvider


@pytest.mark.integration
def test_baostock_detail_maotai():
    d = BaostockProvider().get_instrument_detail("600519.SH")
    assert d.industry is not None
    assert d.pe_ttm is not None and d.pe_ttm > 0
    assert d.pb_mrq is not None and d.pb_mrq > 0
```

Run: `cd backend && uv run pytest tests/test_baostock_detail_integration.py -m integration -v`
Expected: PASS（需联网；若数据源抖动可重试）

- [ ] **Step 4: 门禁 + Commit**

```bash
cd backend && uv run ruff check . && uv run ruff format . && uv run mypy app
git add backend/app/providers/baostock_provider.py backend/tests/test_baostock_detail_integration.py
git commit -m "feat(baostock): implement get_instrument_detail (industry + pe/pb)"
```

---

## Task 4: 后端 AKShare — get_instrument_detail（市值）

**Files:**
- Modify: `backend/app/providers/akshare_provider.py`

**Interfaces:**
- Produces: `AkshareProvider.get_instrument_detail(symbol) -> InstrumentDetail`（total_mv/circ_mv，其余 None）。

**注意（[[data-source-findings]] 坑 2）：** `stock_individual_info_em` 走 eastmoney，可能在本机限流。已有 `_retry`（4 次退避）兜底；失败时服务层会吞掉异常、市值留空，前端显示「—」。这是本期可接受的取舍。

- [ ] **Step 1: 补 import**

`from app.symbols import to_akshare_daily` 改为 `from app.symbols import to_akshare, to_akshare_daily`；
`from .base import Bar, DataProvider, Instrument` 改为 `from .base import Bar, DataProvider, Instrument, InstrumentDetail`。

- [ ] **Step 2: 加方法**（`AkshareProvider` 类内，`list_instruments` 之后）

```python
    def get_instrument_detail(self, symbol: str) -> InstrumentDetail:
        code = to_akshare(symbol)  # 纯 6 位
        df = _retry(lambda: ak.stock_individual_info_em(symbol=code), "individual-info")
        info = dict(zip(df["item"], df["value"], strict=False))
        return InstrumentDetail(
            total_mv=_num(info.get("总市值")),
            circ_mv=_num(info.get("流通市值")),
        )
```

并在模块级 `_dec` 之后加数值解析辅助（市值是数字/字符串，转 float，失败/缺失返回 None）：

```python
def _num(v: object) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
```

- [ ] **Step 3: 触网冒烟测试**（integration）`backend/tests/test_akshare_detail_integration.py`

```python
import pytest

from app.providers.akshare_provider import AkshareProvider


@pytest.mark.integration
def test_akshare_detail_maotai_market_cap():
    d = AkshareProvider().get_instrument_detail("600519.SH")
    assert d.total_mv is not None and d.total_mv > 0
    assert d.circ_mv is not None and d.circ_mv > 0
```

Run: `cd backend && uv run pytest tests/test_akshare_detail_integration.py -m integration -v`
Expected: PASS（若 eastmoney 限流则可能失败/重试；非阻塞）

- [ ] **Step 4: 门禁 + Commit**

```bash
cd backend && uv run ruff check . && uv run ruff format . && uv run mypy app
git add backend/app/providers/akshare_provider.py backend/tests/test_akshare_detail_integration.py
git commit -m "feat(akshare): implement get_instrument_detail (market cap via eastmoney)"
```

---

## Task 5: 后端路由 — GET /api/instrument/{symbol}

**Files:**
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_instrument_route.py`

**Interfaces:**
- Consumes: `get_instrument_detail`（Task 2）、`get_providers`、`get_session`、`UnknownSymbol`。
- Produces: `GET /api/instrument/{symbol}` → `InstrumentDetailOut`。

- [ ] **Step 1: 写失败测试** `backend/tests/test_instrument_route.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.api import routes
from app.main import app
from app.services.market_data import InstrumentDetailResult, UnknownSymbol


@pytest.mark.asyncio
async def test_instrument_route_ok(monkeypatch):
    from datetime import date

    async def _fake(session, providers, symbol):
        return InstrumentDetailResult(
            symbol=symbol, name="贵州茅台", market="SH", type="stock",
            ipo_date=date(2001, 8, 27), industry="白酒",
            pe_ttm=32.5, pb_mrq=9.8, total_mv=1.98e12, circ_mv=1.98e12,
        )

    monkeypatch.setattr(routes, "get_instrument_detail", _fake)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/api/instrument/600519.SH")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "贵州茅台"
    assert body["industry"] == "白酒"
    assert body["total_mv"] == 1.98e12


@pytest.mark.asyncio
async def test_instrument_route_unknown(monkeypatch):
    async def _fake(session, providers, symbol):
        raise UnknownSymbol(symbol)

    monkeypatch.setattr(routes, "get_instrument_detail", _fake)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/api/instrument/000000.SH")
    assert r.status_code == 404
```

> 若现有测试对 DB 会话有统一 fixture/override，照现有 `tests/` 的既有模式接入（参考同目录 kline/compare 路由测试的 `app.dependency_overrides`）。

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && uv run pytest tests/test_instrument_route.py -v`
Expected: FAIL（404 路由不存在 / import 失败）

- [ ] **Step 3: 实现**（`routes.py`）

import 追加 `get_instrument_detail`：把
`from app.services.market_data import (ProviderUnavailable, UnknownSymbol, compare, get_kline,)`
改为加入 `get_instrument_detail`。

在 `/search` 路由之后追加：

```python
class InstrumentDetailOut(BaseModel):
    symbol: str
    name: str
    market: str
    type: str
    ipo_date: date | None
    industry: str | None
    pe_ttm: float | None
    pb_mrq: float | None
    total_mv: float | None
    circ_mv: float | None


@router.get("/instrument/{symbol}", response_model=InstrumentDetailOut)
async def instrument_detail(
    session: Annotated[AsyncSession, Depends(get_session)],
    providers: Annotated[list[DataProvider], Depends(get_providers)],
    symbol: str,
) -> InstrumentDetailOut:
    try:
        r = await get_instrument_detail(session, providers, symbol)
    except UnknownSymbol as exc:
        raise HTTPException(status_code=404, detail=f"未知标的: {exc}") from exc
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"数据源暂不可用: {exc}") from exc
    return InstrumentDetailOut(
        symbol=r.symbol, name=r.name, market=r.market, type=r.type,
        ipo_date=r.ipo_date, industry=r.industry, pe_ttm=r.pe_ttm,
        pb_mrq=r.pb_mrq, total_mv=r.total_mv, circ_mv=r.circ_mv,
    )
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && uv run pytest tests/test_instrument_route.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 全量门禁 + Commit**

```bash
cd backend && uv run ruff check . && uv run ruff format . && uv run mypy app && uv run pytest -m "not integration"
git add backend/app/api/routes.py backend/tests/test_instrument_route.py
git commit -m "feat(api): add GET /api/instrument/{symbol}"
```

---

## Task 6: 前端 — deriveQuote 纯函数 + vitest

**Files:**
- Create: `frontend/src/utils/quote.ts`
- Create: `frontend/src/utils/quote.test.ts`
- Modify: `frontend/package.json`（devDep `vitest` + `"test": "vitest run"`）
- Modify: `frontend/vite.config.ts`（test 块）

**Interfaces:**
- Produces: `deriveQuote(bars: ApiBar[]) -> QuoteSummary | null`；`QuoteSummary{last,changePct,open,high,low,prevClose,volume,amount,amplitude,high52,low52}`。

- [ ] **Step 1: 装 vitest**

Run: `cd frontend && npm i -D vitest`
Expected: 安装成功，`package.json` devDependencies 出现 `vitest`。

- [ ] **Step 2: 加 test 脚本**（`frontend/package.json` scripts 内加一行）

```json
    "test": "vitest run"
```

- [ ] **Step 3: vite.config.ts 顶部加 vitest 引用 + test 块**

在文件首行加 `/// <reference types="vitest" />`，并在 `defineConfig({ ... })` 内加：

```ts
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
```

- [ ] **Step 4: 写失败测试** `frontend/src/utils/quote.test.ts`

```ts
import { describe, expect, it } from 'vitest'
import type { ApiBar } from '../types/kline'
import { deriveQuote } from './quote'

function bar(date: string, o: number, h: number, l: number, c: number): ApiBar {
  return { date, open: o, high: h, low: l, close: c, volume: 100, amount: 1000, trade_status: 1 }
}

describe('deriveQuote', () => {
  it('空数组返回 null', () => {
    expect(deriveQuote([])).toBeNull()
  })

  it('单根：prevClose/changePct 为 null，52 周取自身', () => {
    const q = deriveQuote([bar('2026-01-02', 10, 12, 9, 11)])!
    expect(q.last).toBe(11)
    expect(q.prevClose).toBeNull()
    expect(q.changePct).toBeNull()
    expect(q.high52).toBe(12)
    expect(q.low52).toBe(9)
  })

  it('两根：涨跌幅与振幅按昨收算', () => {
    const q = deriveQuote([bar('2026-01-02', 10, 11, 9, 10), bar('2026-01-03', 10, 13, 10, 12)])!
    expect(q.changePct).toBeCloseTo(20) // (12-10)/10*100
    expect(q.amplitude).toBeCloseTo(30) // (13-10)/10*100
    expect(q.high52).toBe(13)
    expect(q.low52).toBe(9)
  })
})
```

- [ ] **Step 5: 跑测试确认失败**

Run: `cd frontend && npm test`
Expected: FAIL（`quote.ts` 不存在 / `deriveQuote` 未定义）

- [ ] **Step 6: 实现** `frontend/src/utils/quote.ts`

```ts
import type { ApiBar } from '../types/kline'

export interface QuoteSummary {
  last: number
  changePct: number | null // 涨跌幅(%)，无昨收时 null
  open: number
  high: number
  low: number
  prevClose: number | null
  volume: number | null
  amount: number | null
  amplitude: number | null // 振幅(%) = (最高-最低)/昨收*100
  high52: number | null
  low52: number | null
}

const WINDOW = 250 // 约一年交易日

export function deriveQuote(bars: ApiBar[]): QuoteSummary | null {
  if (bars.length === 0) return null
  const last = bars[bars.length - 1]
  const prevClose = bars.length >= 2 ? bars[bars.length - 2].close : null
  const changePct = prevClose ? ((last.close - prevClose) / prevClose) * 100 : null
  const amplitude = prevClose ? ((last.high - last.low) / prevClose) * 100 : null
  const window = bars.slice(-WINDOW)
  const high52 = Math.max(...window.map((b) => b.high))
  const low52 = Math.min(...window.map((b) => b.low))
  return {
    last: last.close,
    changePct,
    open: last.open,
    high: last.high,
    low: last.low,
    prevClose,
    volume: last.volume,
    amount: last.amount,
    amplitude,
    high52,
    low52,
  }
}
```

- [ ] **Step 7: 跑测试确认通过**

Run: `cd frontend && npm test`
Expected: PASS（3 passed）

- [ ] **Step 8: Commit**

```bash
git add frontend/src/utils/quote.ts frontend/src/utils/quote.test.ts frontend/package.json frontend/package-lock.json frontend/vite.config.ts
git commit -m "feat(frontend): deriveQuote pure fn + vitest for quote summary"
```

---

## Task 7: 前端 — instrument API + useInstrument composable

**Files:**
- Create: `frontend/src/api/instrument.ts`
- Create: `frontend/src/composables/useInstrument.ts`

**Interfaces:**
- Produces: `InstrumentDetail`（TS 接口，字段同后端 `InstrumentDetailOut`）；`fetchInstrument(symbol) -> Promise<InstrumentDetail>`；`useInstrument(symbol: Ref<string>) -> { detail, loading, error }`。

- [ ] **Step 1: 写 api** `frontend/src/api/instrument.ts`

```ts
import axios from 'axios'

export interface InstrumentDetail {
  symbol: string
  name: string
  market: string
  type: string
  ipo_date: string | null
  industry: string | null
  pe_ttm: number | null
  pb_mrq: number | null
  total_mv: number | null
  circ_mv: number | null
}

// 调后端 GET /api/instrument/{symbol}：低频基本面（name/市场/上市日 + PE/PB/行业/市值）
export async function fetchInstrument(symbol: string): Promise<InstrumentDetail> {
  const { data } = await axios.get<InstrumentDetail>(`/api/instrument/${symbol}`)
  return data
}
```

- [ ] **Step 2: 写 composable** `frontend/src/composables/useInstrument.ts`

```ts
import { ref, watch, type Ref } from 'vue'
import { fetchInstrument, type InstrumentDetail } from '../api/instrument'

// 详情随 symbol 变化重取；失败不致命（detail=null，前端显示「—」）
export function useInstrument(symbol: Ref<string>) {
  const detail = ref<InstrumentDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function reload() {
    const sym = symbol.value.trim()
    if (!sym) {
      detail.value = null
      return
    }
    loading.value = true
    error.value = null
    try {
      detail.value = await fetchInstrument(sym)
    } catch {
      detail.value = null
      error.value = '详情加载失败'
    } finally {
      loading.value = false
    }
  }

  watch(symbol, reload, { immediate: true })

  return { detail, loading, error }
}
```

- [ ] **Step 3: 类型检查**

Run: `cd frontend && npx vue-tsc -b`
Expected: PASS（无类型错误）

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/instrument.ts frontend/src/composables/useInstrument.ts
git commit -m "feat(frontend): instrument detail api + useInstrument composable"
```

---

## Task 8: 前端 — StockDetail.vue（信息条）

**Files:**
- Create: `frontend/src/components/StockDetail.vue`

**Interfaces:**
- Consumes: `deriveQuote`（Task 6）、`InstrumentDetail`（Task 7）、`ApiBar`。
- Produces: `<StockDetail :symbol :bars :detail />` — 纯展示，无副作用。

- [ ] **Step 1: 写组件** `frontend/src/components/StockDetail.vue`

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { InstrumentDetail } from '../api/instrument'
import { deriveQuote } from '../utils/quote'
import type { ApiBar } from '../types/kline'

const props = defineProps<{
  symbol: string
  bars: ApiBar[]
  detail: InstrumentDetail | null
}>()

const q = computed(() => deriveQuote(props.bars))
const name = computed(() => props.detail?.name ?? props.symbol)
const up = computed(() => (q.value?.changePct ?? 0) >= 0)

function pct(v: number | null): string {
  return v === null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
function num(v: number | null, digits = 2): string {
  return v === null ? '—' : v.toFixed(digits)
}
// 市值(元) → 亿/万亿
function money(v: number | null): string {
  if (v === null) return '—'
  if (v >= 1e12) return `${(v / 1e12).toFixed(2)}万亿`
  return `${(v / 1e8).toFixed(2)}亿`
}
// 成交额(元) → 亿；成交量(手)
function amount(v: number | null): string {
  return v === null ? '—' : `${(v / 1e8).toFixed(2)}亿`
}
function vol(v: number | null): string {
  return v === null ? '—' : `${(v / 1e4).toFixed(1)}万手`
}
</script>

<template>
  <div class="detail">
    <div class="head">
      <span class="name">{{ name }}</span>
      <span class="sym">{{ symbol }}</span>
      <span v-if="detail?.industry" class="tag">{{ detail.industry }}</span>
    </div>

    <div class="quote">
      <span class="price" :class="up ? 'up' : 'down'">{{ num(q?.last ?? null) }}</span>
      <span class="chg" :class="up ? 'up' : 'down'">{{ pct(q?.changePct ?? null) }}</span>
    </div>

    <div class="grid">
      <span>今开 <b>{{ num(q?.open ?? null) }}</b></span>
      <span>最高 <b>{{ num(q?.high ?? null) }}</b></span>
      <span>最低 <b>{{ num(q?.low ?? null) }}</b></span>
      <span>昨收 <b>{{ num(q?.prevClose ?? null) }}</b></span>
      <span>振幅 <b>{{ pct(q?.amplitude ?? null) }}</b></span>
      <span>量 <b>{{ vol(q?.volume ?? null) }}</b></span>
      <span>额 <b>{{ amount(q?.amount ?? null) }}</b></span>
      <span>52周 <b>{{ num(q?.low52 ?? null) }}~{{ num(q?.high52 ?? null) }}</b></span>
      <span>PE <b>{{ num(detail?.pe_ttm ?? null) }}</b></span>
      <span>PB <b>{{ num(detail?.pb_mrq ?? null) }}</b></span>
      <span>总市值 <b>{{ money(detail?.total_mv ?? null) }}</b></span>
      <span>流通 <b>{{ money(detail?.circ_mv ?? null) }}</b></span>
      <span>上市 <b>{{ detail?.ipo_date ?? '—' }}</b></span>
    </div>
  </div>
</template>

<style scoped>
.detail {
  padding: var(--space-3);
  border-bottom: 1px solid var(--c-border);
}
.head {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}
.name {
  font-size: var(--fs-md);
  font-weight: var(--fw-semibold);
}
.sym {
  color: var(--c-text-tertiary);
  font-size: var(--fs-sm);
}
.tag {
  font-size: var(--fs-caption);
  color: var(--c-text-secondary);
  background: var(--c-surface-50);
  border-radius: var(--radius-sm);
  padding: 0 var(--space-2);
}
.quote {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin: var(--space-2) 0;
}
.price {
  font-size: var(--fs-xl);
  font-weight: var(--fw-semibold);
}
.chg {
  font-size: var(--fs-md);
}
.up {
  color: var(--c-danger, #d33);
}
.down {
  color: var(--c-success, #22a);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: var(--space-1) var(--space-4);
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
}
.grid b {
  color: var(--c-text);
  font-weight: var(--fw-medium);
}
</style>
```

> A 股惯例涨红跌绿：涨用 `--c-danger`（红），跌用 `--c-success`（绿）。若设计 token 无此语义变量，落地时改用 `tokens.css` 里实际的红/绿变量名（实现时查 `src/styles/tokens.css` 确认）。

- [ ] **Step 2: 类型检查**

Run: `cd frontend && npx vue-tsc -b`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/StockDetail.vue
git commit -m "feat(frontend): StockDetail info bar component"
```

---

## Task 9: 前端 — 接入 MarketView 单股态 + 导航栏改造

**Files:**
- Modify: `frontend/src/views/MarketView.vue`
- Modify: `frontend/src/views/HomeView.vue`

**Interfaces:**
- Consumes: `StockDetail`（Task 8）、`useInstrument`（Task 7）。

- [ ] **Step 1: MarketView 引入详情**

在 `<script setup>` import 段加：

```ts
import StockDetail from '../components/StockDetail.vue'
import { useInstrument } from '../composables/useInstrument'
```

在 `const { bars, loading: sLoading, error: sError } = useKline(primary, period, adjust)` 之后加：

```ts
const { detail } = useInstrument(primary)
```

在单股态模板里，把 `<ChartToolbar ... />` 之前插入：

```vue
      <StockDetail :symbol="primary" :bars="bars" :detail="detail" />
```

（即单股 `<template v-else-if="!isCompare">` 内、`ChartToolbar` 上方）

- [ ] **Step 2: HomeView 导航栏改造**

把 topbar 模板：

```vue
    <header class="topbar">
      <h1>股票复盘</h1>
      <SearchBox />
      <div class="user">
```

改为（去掉 `<h1>`，搜索框占最左）：

```vue
    <header class="topbar">
      <SearchBox />
      <div class="user">
```

并删除 `<style>` 中不再使用的 `.topbar h1 { ... }` 规则块。

- [ ] **Step 3: 类型检查 + 构建**

Run: `cd frontend && npx vue-tsc -b`
Expected: PASS（无未使用 import / 类型错误）

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/MarketView.vue frontend/src/views/HomeView.vue
git commit -m "feat(frontend): wire StockDetail into single-stock view; search-left navbar"
```

---

## Task 10: 端到端驱动验证

**Files:** 无（验证）

- [ ] **Step 1: 确认本地服务在跑**（后端 8000 / 前端 5174 / Postgres 5433）。若未跑，按 `backend/README.md` 启动。

- [ ] **Step 2: 后端接口冒烟**

Run: `curl -s "http://127.0.0.1:8000/api/instrument/600519.SH" | python3 -m json.tool`
Expected: 200，含 `name/industry/pe_ttm/pb_mrq`；`total_mv/circ_mv` 有值或为 `null`（eastmoney 限流时 null，可接受）。

- [ ] **Step 3: 用 `/run` 或 chromium-cli 打开 http://localhost:5174**，登录后在导航栏最左搜索「茅台」→ 点选 → 右侧应显示：信息条（名称/代码/行业 + 现价/涨跌幅 + 今开/最高/最低/昨收/振幅/量额/52周/PE/PB/市值/上市）在上，K 线在下。**看截图确认信息条渲染正常、涨红跌绿、无横向滚动溢出。**

- [ ] **Step 4: 回归对比态**：左侧勾选 ≥2 只 → 右侧仍为归一化对比图（不受影响）。

- [ ] **Step 5: 全量门禁**

Run: `cd backend && uv run ruff check . && uv run mypy app && uv run pytest -m "not integration"` 且 `cd frontend && npm test && npx vue-tsc -b`
Expected: 全 PASS。

---

## Self-Review 记录

- **Spec 覆盖**：导航栏(Task9)、右侧信息条+K线(Task8/9)、报价派生(Task6)、基本面接口(Task1-5)、市值备源(Task4)、对比保留(Task9 Step4 回归)、测试策略(服务层 Task2 / 纯函数 Task6) — 均有对应任务。
- **占位符**：无 TODO/TBD；每步含实际代码/命令。
- **类型一致**：`InstrumentDetail`(provider) vs `InstrumentDetailResult`(service) vs `InstrumentDetailOut`(route) vs `InstrumentDetail`(前端 TS 接口) 字段对齐；`deriveQuote`/`QuoteSummary` 前后一致。
- **已知取舍**：市值走 eastmoney 可能限流 → 服务层吞异常、前端「—」，本期接受（[[data-source-findings]]）；涨跌色 token 名以 `tokens.css` 实际为准。
