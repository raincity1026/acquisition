"""账号与自选路由：/api/auth/*、/api/me、/api/watchlist。"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import DataProvider
from app.services import accounts
from app.storage import repository as repo
from app.storage.database import get_session

from .deps import CurrentUser
from .routes import get_providers

router = APIRouter(prefix="/api")


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    user_id: int
    email: str


class WatchItemOut(BaseModel):
    symbol: str
    name: str
    last_close: float | None
    change_pct: float | None
    group_ids: list[int]


class AddWatchIn(BaseModel):
    symbol: str


class GroupOut(BaseModel):
    id: int
    name: str


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class SetGroupsIn(BaseModel):
    group_ids: list[int]


@router.post("/auth/register", response_model=TokenOut)
async def register(
    body: Credentials, session: Annotated[AsyncSession, Depends(get_session)]
) -> TokenOut:
    try:
        token = await accounts.register(session, body.email, body.password)
    except accounts.EmailTaken as exc:
        raise HTTPException(status_code=409, detail="该邮箱已注册") from exc
    return TokenOut(access_token=token)


@router.post("/auth/login", response_model=TokenOut)
async def login(
    body: Credentials, session: Annotated[AsyncSession, Depends(get_session)]
) -> TokenOut:
    try:
        token = await accounts.login(session, body.email, body.password)
    except accounts.InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail="邮箱或密码错误") from exc
    return TokenOut(access_token=token)


@router.get("/me", response_model=MeOut)
async def me(user_id: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]) -> MeOut:
    email = await repo.get_user_email(session, user_id)
    if email is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return MeOut(user_id=user_id, email=email)


@router.get("/watchlist", response_model=list[WatchItemOut])
async def get_watchlist(
    user_id: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]
) -> list[WatchItemOut]:
    items = await accounts.get_watchlist(session, user_id)
    return [
        WatchItemOut(
            symbol=i.symbol,
            name=i.name,
            last_close=i.last_close,
            change_pct=i.change_pct,
            group_ids=i.group_ids,
        )
        for i in items
    ]


@router.get("/watchlist/groups", response_model=list[GroupOut])
async def list_groups(
    user_id: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]
) -> list[GroupOut]:
    return [
        GroupOut(id=gid, name=name) for gid, name in await accounts.list_groups(session, user_id)
    ]


@router.post("/watchlist/groups", response_model=GroupOut, status_code=201)
async def create_group(
    body: GroupIn, user_id: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]
) -> GroupOut:
    try:
        gid, name = await accounts.create_group(session, user_id, body.name)
    except accounts.GroupNameTaken as exc:
        raise HTTPException(status_code=409, detail="分组名已存在") from exc
    return GroupOut(id=gid, name=name)


@router.patch("/watchlist/groups/{group_id}", status_code=204)
async def rename_group(
    group_id: int,
    body: GroupIn,
    user_id: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        await accounts.rename_group(session, user_id, group_id, body.name)
    except accounts.GroupNotFound as exc:
        raise HTTPException(status_code=404, detail="分组不存在") from exc
    except accounts.GroupNameTaken as exc:
        raise HTTPException(status_code=409, detail="分组名已存在") from exc


@router.delete("/watchlist/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int, user_id: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]
) -> None:
    try:
        await accounts.delete_group(session, user_id, group_id)
    except accounts.GroupNotFound as exc:
        raise HTTPException(status_code=404, detail="分组不存在") from exc


@router.put("/watchlist/{symbol}/groups", status_code=204)
async def set_symbol_groups(
    symbol: str,
    body: SetGroupsIn,
    user_id: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        await accounts.set_symbol_groups(session, user_id, symbol, body.group_ids)
    except accounts.SymbolNotWatched as exc:
        raise HTTPException(status_code=404, detail="该标的不在自选中") from exc


@router.post("/watchlist", status_code=201)
async def add_watchlist(
    body: AddWatchIn,
    background: BackgroundTasks,
    user_id: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    providers: Annotated[list[DataProvider], Depends(get_providers)],
) -> dict[str, str]:
    if await repo.get_instrument(session, body.symbol) is None:
        raise HTTPException(status_code=404, detail=f"未知标的: {body.symbol}")
    await repo.add_watch(session, user_id, body.symbol)
    # 异步把行情抓进库，不阻塞响应
    background.add_task(accounts.prefetch_symbol, providers, body.symbol)
    return {"status": "ok"}


@router.delete("/watchlist/{symbol}", status_code=204)
async def remove_watchlist(
    symbol: str,
    user_id: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    await repo.remove_watch(session, user_id, symbol)
