"""M3 账号 + 自选 验收（真实 PostgreSQL + ASGI）。标记 integration（需 docker PG）。"""

from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.routes import get_providers
from app.main import app
from app.providers.base import Bar, DataProvider, Instrument
from app.storage import repository as repo
from app.storage.database import SessionMaker, engine

pytestmark = pytest.mark.integration

SYM = "600519.SH"


class _NoNet(DataProvider):  # prefetch 后台任务用，不触网
    def get_daily_bars(self, symbol: str, start: date, end: date) -> list[Bar]:
        return []

    def list_instruments(self) -> list[Instrument]:
        return []

    def get_trade_calendar(self, start: date, end: date) -> list[date]:
        return []


def _bar(d: str, raw: float) -> Bar:
    v = Decimal(str(raw))
    return Bar(date.fromisoformat(d), v, v, v, v, Decimal("1"), Decimal("1"), v, 1)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE watchlist, users, daily_bars, instruments RESTART IDENTITY CASCADE")
        )
    async with SessionMaker() as s:  # 预置标的 + 行情(供自选显示报价)
        await repo.upsert_instruments(
            s, [Instrument(SYM, "贵州茅台", "SH", "stock", None, "listing")]
        )
        await repo.upsert_bars(s, SYM, [_bar("2024-12-30", 1500), _bar("2024-12-31", 1530)])
    app.dependency_overrides[get_providers] = lambda: [_NoNet()]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def _token(c: AsyncClient, email: str) -> str:
    r = await c.post("/api/auth/register", json={"email": email, "password": "secret123"})
    assert r.status_code == 200
    return r.json()["access_token"]


async def test_register_hashes_password(client: AsyncClient) -> None:
    await _token(client, "a@x.com")
    async with SessionMaker() as s:
        ph = (
            await s.execute(text("SELECT password_hash FROM users WHERE email='a@x.com'"))
        ).scalar_one()
    assert ph != "secret123" and "secret123" not in ph  # 哈希，无明文


async def test_login_and_me(client: AsyncClient) -> None:
    await _token(client, "b@x.com")
    r = await client.post("/api/auth/login", json={"email": "b@x.com", "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == "b@x.com"
    # 密码错误
    bad = await client.post("/api/auth/login", json={"email": "b@x.com", "password": "nope12"})
    assert bad.status_code == 401


async def test_watchlist_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/watchlist")).status_code == 401


async def test_watchlist_crud_and_quote(client: AsyncClient) -> None:
    token = await _token(client, "c@x.com")
    h = {"Authorization": f"Bearer {token}"}
    assert (await client.post("/api/watchlist", json={"symbol": SYM}, headers=h)).status_code == 201
    wl = (await client.get("/api/watchlist", headers=h)).json()
    assert len(wl) == 1
    assert wl[0]["symbol"] == SYM and wl[0]["name"] == "贵州茅台"
    assert wl[0]["last_close"] == 1530.0
    assert wl[0]["change_pct"] == 2.0  # (1530/1500-1)*100
    # 删除
    assert (await client.delete(f"/api/watchlist/{SYM}", headers=h)).status_code == 204
    assert (await client.get("/api/watchlist", headers=h)).json() == []


async def test_watchlist_isolated_between_users(client: AsyncClient) -> None:
    t1 = await _token(client, "u1@x.com")
    t2 = await _token(client, "u2@x.com")
    await client.post(
        "/api/watchlist", json={"symbol": SYM}, headers={"Authorization": f"Bearer {t1}"}
    )
    # u2 看不到 u1 的自选
    wl2 = (await client.get("/api/watchlist", headers={"Authorization": f"Bearer {t2}"})).json()
    assert wl2 == []
    # 重复邮箱注册被拒
    dup = await client.post(
        "/api/auth/register", json={"email": "u1@x.com", "password": "secret123"}
    )
    assert dup.status_code == 409
