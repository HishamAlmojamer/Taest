import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update, or_
from app.config import settings
from app.database import get_db, async_session_factory
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.rbac import Role, Permission, role_permissions
from app.models.accounting import FiscalPeriod
from app.models.core import Branch
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse, ChangePasswordRequest, RefreshTokenRequest
from app.schemas.common import MessageResponse
from app.utils.security import (
    verify_password, hash_password, _is_old_hash,
    create_access_token, create_refresh_token, decode_token,
)
from app.utils.deps import get_current_user
from datetime import UTC, datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def _store_refresh_token(db: AsyncSession, user_id: int, token: str) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    await db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
    db.add(
        RefreshToken(
            user_id=user_id,
            token=_hash_refresh_token(token),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.flush()


async def _get_user_permissions(db: AsyncSession, user: User) -> list[str]:
    """Get permission codes for a user via their role_id or role string."""
    # Try role_id first (new RBAC system)
    if user.role_id:
        result = await db.execute(
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == user.role_id)
        )
        codes = [row[0] for row in result.all()]
        if codes:
            return codes

    # Fallback: match by role string name
    role_result = await db.execute(select(Role).where(Role.name == user.role))
    role = role_result.scalar_one_or_none()
    if role:
        result = await db.execute(
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role.id)
        )
        codes = [row[0] for row in result.all()]
        if codes:
            return codes

    # Hardcoded fallback for backward compatibility
    legacy_permissions = {
        "admin": [
            "CREATE_SALE", "EDIT_SALE", "DELETE_SALE", "APPROVE_SALE", "VIEW_SALE",
            "CREATE_PURCHASE", "EDIT_PURCHASE", "DELETE_PURCHASE", "APPROVE_PURCHASE", "VIEW_PURCHASE",
            "CREATE_JOURNAL", "EDIT_JOURNAL", "DELETE_JOURNAL", "POST_JOURNAL", "VIEW_JOURNAL",
            "VIEW_REPORTS", "MANAGE_USERS", "MANAGE_SETTINGS", "MANAGE_ASSETS", "MANAGE_BUDGETS",
            "RECONCILE_BANK", "VIEW_AGING_REPORTS",
        ],
        "accountant": [
            "CREATE_SALE", "EDIT_SALE", "VIEW_SALE",
            "CREATE_PURCHASE", "EDIT_PURCHASE", "VIEW_PURCHASE",
            "CREATE_JOURNAL", "EDIT_JOURNAL", "POST_JOURNAL", "VIEW_JOURNAL",
            "VIEW_REPORTS", "MANAGE_ASSETS", "MANAGE_BUDGETS", "RECONCILE_BANK", "VIEW_AGING_REPORTS",
        ],
        "manager": [
            "CREATE_SALE", "EDIT_SALE", "APPROVE_SALE", "VIEW_SALE",
            "CREATE_PURCHASE", "EDIT_PURCHASE", "APPROVE_PURCHASE", "VIEW_PURCHASE",
            "VIEW_JOURNAL", "VIEW_REPORTS", "MANAGE_BUDGETS", "VIEW_AGING_REPORTS",
        ],
        "viewer": ["VIEW_SALE", "VIEW_PURCHASE", "VIEW_JOURNAL", "VIEW_REPORTS", "VIEW_AGING_REPORTS"],
    }
    return legacy_permissions.get(user.role, legacy_permissions["viewer"])


@router.get("/context")
async def get_login_context(db: AsyncSession = Depends(get_db)):
    """Public context for the login screen: active fiscal periods and branches.

    This endpoint requires no authentication so the login page can populate
    the financial year and branch dropdowns before the user signs in.
    """
    periods_result = await db.execute(
        select(FiscalPeriod)
        .where(or_(FiscalPeriod.is_closed.is_(None), FiscalPeriod.is_closed == False))
        .order_by(FiscalPeriod.start_date.desc())
    )
    branches_result = await db.execute(
        select(Branch)
        .where(or_(Branch.is_active.is_(None), Branch.is_active == True))
        .order_by(Branch.name)
    )
    fiscal_periods = [
        {
            "id": fp.id,
            "name": fp.name,
            "start_date": str(fp.start_date) if fp.start_date else None,
            "end_date": str(fp.end_date) if fp.end_date else None,
            "is_closed": fp.is_closed,
            "is_locked": fp.is_locked,
        }
        for fp in periods_result.scalars().all()
    ]
    branches = [
        {
            "id": b.id,
            "name": b.name,
            "code": b.code,
            "company_id": b.company_id,
        }
        for b in branches_result.scalars().all()
    ]
    return {"fiscal_periods": fiscal_periods, "branches": branches}


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()

    # Brute-force protection: soft-lock the account after repeated failures.
    if user and user.locked_until:
        if datetime.now(UTC).replace(tzinfo=None) < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="الحساب مقفل مؤقتاً بسبب محاولات دخول فاشلة متكررة، حاول لاحقاً",
            )
        # Lock expired: reset the counters.
        await db.execute(update(User).where(User.id == user.id).values(
            failed_login_attempts=0, locked_until=None,
        ))
        await db.flush()

    if not user or not verify_password(req.password, user.password):
        # Record the failed attempt (if the user exists) and lock after the cap.
        # This MUST persist even though we raise an HTTPException below (the
        # request-scoped session rolls back on exceptions), so it runs in its
        # own committed session.
        if user:
            try:
                async with async_session_factory() as sess:
                    current = (await sess.execute(
                        select(User).where(User.id == user.id)
                    )).scalar_one_or_none()
                    if current:
                        attempts = (current.failed_login_attempts or 0) + 1
                        lock = None
                        if attempts >= 5:
                            lock = (datetime.now(UTC).replace(tzinfo=None)
                                    + timedelta(minutes=15))
                            attempts = 5
                        await sess.execute(update(User).where(User.id == user.id).values(
                            failed_login_attempts=attempts, locked_until=lock,
                        ))
                        await sess.commit()
            except Exception:
                logger.exception("Failed to record login attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    # Successful login resets the failure counters.
    if (user.failed_login_attempts or 0) or user.locked_until:
        await db.execute(update(User).where(User.id == user.id).values(
            failed_login_attempts=0, locked_until=None,
        ))
        await db.flush()

    # Auto-migrate old SHA-1/SHA-256 hashes to bcrypt
    if _is_old_hash(user.password):
        new_hash = hash_password(req.password)
        await db.execute(update(User).where(User.id == user.id).values(
            password=new_hash,
            last_login_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    else:
        await db.execute(update(User).where(User.id == user.id).values(
            last_login_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    await db.flush()

    token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    await _store_refresh_token(db, user.id, refresh_token)

    permissions = await _get_user_permissions(db, user)
    user_response = UserResponse.model_validate(user)
    user_response.permissions = permissions

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Consume the stored token atomically: a refresh token can be used once.
    # Reusing an already-rotated token (or one issued before server-side
    # tracking existed) is rejected.
    consumed = await db.execute(
        delete(RefreshToken).where(
            RefreshToken.token == _hash_refresh_token(req.refresh_token),
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > datetime.now(UTC).replace(tzinfo=None),
        )
    )
    if consumed.rowcount != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_data = {"sub": str(user.id), "username": user.username, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    await _store_refresh_token(db, user.id, refresh_token)

    permissions = await _get_user_permissions(db, user)
    user_response = UserResponse.model_validate(user)
    user_response.permissions = permissions

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Revoke a refresh token (idempotent)."""
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token == _hash_refresh_token(req.refresh_token))
    )
    return MessageResponse(message="Logged out successfully")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    permissions = await _get_user_permissions(db, current_user)
    user_response = UserResponse.model_validate(current_user)
    user_response.permissions = permissions
    return user_response


@router.put("/password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="كلمة المرور يجب أن تكون 8 أحرف على الأقل")
    if req.new_password == req.old_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="كلمة المرور الجديدة يجب أن تختلف عن القديمة")
    new_hash = hash_password(req.new_password)
    await db.execute(update(User).where(User.id == current_user.id).values(password=new_hash))
    # Force every other session to sign in again with the new password.
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == current_user.id))
    return MessageResponse(message="Password changed successfully")
