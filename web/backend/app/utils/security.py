import bcrypt
import hashlib
from jose import jwt
from datetime import UTC, datetime, timedelta
from app.config import settings


def _is_old_hash(hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return hashed_password.startswith("$2") is False and len(hashed_password) in (40, 64)


def _verify_old_hash(plain_password: str, hashed_password: str) -> bool:
    sha1 = hashlib.sha1(plain_password.encode()).hexdigest()
    sha256 = hashlib.sha256(plain_password.encode()).hexdigest()
    return sha1 == hashed_password or sha256 == hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if _is_old_hash(hashed_password):
        return _verify_old_hash(plain_password, hashed_password)
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def rehash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
