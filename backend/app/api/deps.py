"""认证依赖：从 Authorization: Bearer <jwt> 取出当前 user_id。"""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import InvalidToken, decode_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> int:
    if cred is None:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        return decode_token(cred.credentials)
    except InvalidToken as exc:
        raise HTTPException(status_code=401, detail="无效或过期的凭证") from exc


CurrentUser = Annotated[int, Depends(get_current_user_id)]
