from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.rbac import Role, Permission, role_permissions
from app.utils.security import decode_token

security = HTTPBearer(auto_error=False)


async def _get_user_permissions(db: AsyncSession, user: User) -> set[str]:
    """Get permission codes for a user via role_id or role string."""
    if user.role_id:
        result = await db.execute(
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == user.role_id)
        )
        codes = [row[0] for row in result.all()]
        if codes:
            return set(codes)

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
            return set(codes)

    legacy_permissions = {
        "admin": {
            "CREATE_SALE", "EDIT_SALE", "DELETE_SALE", "APPROVE_SALE", "VIEW_SALE",
            "CREATE_PURCHASE", "EDIT_PURCHASE", "DELETE_PURCHASE", "APPROVE_PURCHASE", "VIEW_PURCHASE",
            "CREATE_JOURNAL", "EDIT_JOURNAL", "DELETE_JOURNAL", "POST_JOURNAL", "VIEW_JOURNAL",
            "VIEW_REPORTS", "MANAGE_USERS", "MANAGE_SETTINGS", "MANAGE_ASSETS", "MANAGE_BUDGETS",
            "RECONCILE_BANK", "VIEW_AGING_REPORTS", "MANAGE_CHEQUES",
            "MANAGE_INVENTORY", "VIEW_INVENTORY", "MANAGE_HR", "VIEW_HR",
            "MANAGE_CRM", "VIEW_CRM", "MANAGE_PROJECTS", "VIEW_PROJECTS",
            "MANAGE_PROMOTIONS", "CREATE_QUOTATION", "EDIT_QUOTATION", "DELETE_QUOTATION",
        },
        "accountant": {
            "CREATE_SALE", "EDIT_SALE", "VIEW_SALE",
            "CREATE_PURCHASE", "EDIT_PURCHASE", "VIEW_PURCHASE",
            "CREATE_JOURNAL", "EDIT_JOURNAL", "POST_JOURNAL", "VIEW_JOURNAL",
            "VIEW_REPORTS", "MANAGE_ASSETS", "MANAGE_BUDGETS", "RECONCILE_BANK", "MANAGE_CHEQUES", "VIEW_AGING_REPORTS",
            "MANAGE_INVENTORY", "VIEW_INVENTORY", "VIEW_HR", "VIEW_CRM",
            "MANAGE_PROJECTS", "VIEW_PROJECTS", "MANAGE_PROMOTIONS",
            "CREATE_QUOTATION", "EDIT_QUOTATION",
        },
        "manager": {
            "CREATE_SALE", "EDIT_SALE", "APPROVE_SALE", "VIEW_SALE",
            "CREATE_PURCHASE", "EDIT_PURCHASE", "APPROVE_PURCHASE", "VIEW_PURCHASE",
            "VIEW_JOURNAL", "VIEW_REPORTS", "MANAGE_BUDGETS", "MANAGE_CHEQUES", "VIEW_AGING_REPORTS",
            "MANAGE_INVENTORY", "VIEW_INVENTORY", "MANAGE_HR", "VIEW_HR",
            "MANAGE_CRM", "VIEW_CRM", "MANAGE_PROJECTS", "VIEW_PROJECTS",
            "MANAGE_PROMOTIONS", "CREATE_QUOTATION", "EDIT_QUOTATION", "DELETE_QUOTATION",
        },
        "viewer": {"VIEW_SALE", "VIEW_PURCHASE", "VIEW_JOURNAL", "VIEW_REPORTS", "VIEW_AGING_REPORTS",
                   "VIEW_INVENTORY", "VIEW_HR", "VIEW_CRM", "VIEW_PROJECTS"},
    }
    return set(legacy_permissions.get(user.role, legacy_permissions["viewer"]))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.is_active is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_active is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_permission(permission: str):
    """Dependency factory — returns a dependency that enforces a permission code.

    Usage: `deps: User = Depends(require_permission("VIEW_JOURNAL"))`
    """
    async def _dep(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        perms = await _get_user_permissions(db, current_user)
        if current_user.role in ("admin", "owner") or "MANAGE_SETTINGS" in perms:
            return current_user
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user
    return _dep
