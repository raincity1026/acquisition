"""自选分组管理验收（真实 test 库 + ASGI）。"""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.routes import get_providers
from app.main import app
from app.providers.base import DataProvider, Instrument
from app.storage import repository as repo
from app.storage.database import SessionMaker, engine

pytestmark = pytest.mark.integration

A, B = "600519.SH", "000858.SZ"


class _NoNet(DataProvider):
    def get_daily_bars(self, symbol, start, end):  # type: ignore[no-untyped-def]
        return []

    def list_instruments(self) -> list[Instrument]:
        return []

    def get_trade_calendar(self, start, end):  # type: ignore[no-untyped-def]
        return []


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE watchlist_group_members, watchlist_groups, watchlist, users, "
                "daily_bars, instruments RESTART IDENTITY CASCADE"
            )
        )
    async with SessionMaker() as s:
        await repo.upsert_instruments(
            s,
            [
                Instrument(A, "贵州茅台", "SH", "stock", None, "listing"),
                Instrument(B, "五粮液", "SZ", "stock", None, "listing"),
            ],
        )
    app.dependency_overrides[get_providers] = lambda: [_NoNet()]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def _auth(c: AsyncClient, email: str) -> dict[str, str]:
    r = await c.post("/api/auth/register", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _gids(c: AsyncClient, h: dict[str, str], symbol: str) -> list[int]:
    wl = (await c.get("/api/watchlist", headers=h)).json()
    return next(i["group_ids"] for i in wl if i["symbol"] == symbol)


async def test_group_crud_and_membership(client: AsyncClient) -> None:
    h = await _auth(client, "g@x.com")
    await client.post("/api/watchlist", json={"symbol": A}, headers=h)
    await client.post("/api/watchlist", json={"symbol": B}, headers=h)

    # 建组
    g1 = (await client.post("/api/watchlist/groups", json={"name": "白酒"}, headers=h)).json()
    g2 = (await client.post("/api/watchlist/groups", json={"name": "重仓"}, headers=h)).json()
    assert {x["name"] for x in (await client.get("/api/watchlist/groups", headers=h)).json()} == {
        "白酒",
        "重仓",
    }
    # 重名 409
    assert (
        await client.post("/api/watchlist/groups", json={"name": "白酒"}, headers=h)
    ).status_code == 409

    # A 同属两个分组（多分组）
    r = await client.put(
        f"/api/watchlist/{A}/groups", json={"group_ids": [g1["id"], g2["id"]]}, headers=h
    )
    assert r.status_code == 204
    assert sorted(await _gids(client, h, A)) == sorted([g1["id"], g2["id"]])
    assert await _gids(client, h, B) == []  # B 未分组 → 默认分组

    # 改名
    assert (
        await client.patch(
            f"/api/watchlist/groups/{g1['id']}", json={"name": "白酒龙头"}, headers=h
        )
    ).status_code == 204

    # 删组 g2 → A 只剩 g1
    assert (await client.delete(f"/api/watchlist/groups/{g2['id']}", headers=h)).status_code == 204
    assert await _gids(client, h, A) == [g1["id"]]

    # 删自选 A → 其分组归属一并清掉（重加后为空）
    await client.delete(f"/api/watchlist/{A}", headers=h)
    await client.post("/api/watchlist", json={"symbol": A}, headers=h)
    assert await _gids(client, h, A) == []


async def test_groups_isolated_between_users(client: AsyncClient) -> None:
    h1 = await _auth(client, "u1@x.com")
    await client.post("/api/watchlist/groups", json={"name": "我的组"}, headers=h1)
    h2 = await _auth(client, "u2@x.com")
    assert (await client.get("/api/watchlist/groups", headers=h2)).json() == []
    # u2 改不了 u1 的组（404）
    g1 = (await client.get("/api/watchlist/groups", headers=h1)).json()[0]
    assert (
        await client.patch(f"/api/watchlist/groups/{g1['id']}", json={"name": "x"}, headers=h2)
    ).status_code == 404


async def test_set_groups_for_unwatched_symbol_404(client: AsyncClient) -> None:
    h = await _auth(client, "n@x.com")
    g = (await client.post("/api/watchlist/groups", json={"name": "组"}, headers=h)).json()
    # A 没加自选就设分组 → 404
    assert (
        await client.put(f"/api/watchlist/{A}/groups", json={"group_ids": [g["id"]]}, headers=h)
    ).status_code == 404
