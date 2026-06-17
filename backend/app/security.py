"""密码哈希(bcrypt) 与 JWT 签发/校验。密码绝不明文存储。"""

import datetime

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.config import settings

_hasher = PasswordHash((BcryptHasher(),))


class InvalidToken(Exception):
    """JWT 缺失/过期/被篡改。"""


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    minutes = settings.jwt_expire_minutes if expires_minutes is None else expires_minutes
    now = datetime.datetime.now(datetime.UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + datetime.timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise InvalidToken(str(exc)) from exc
