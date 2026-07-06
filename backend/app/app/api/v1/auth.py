"""Authentication routes."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.database import get_db
from app.models.branch import Branch
from app.models.employee_branch import EmployeeBranchSession
from app.models.user import User
from app.schemas import (
    BranchResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SelectBranchRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit import log_action
from app.services.branches import employee_can_use_branch, get_active_branches, get_employee_branches, record_branch_session

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


async def _branch_name(db: AsyncSession, branch_id: int | None) -> str | None:
    if not branch_id:
        return None
    branch = await db.get(Branch, branch_id)
    return branch.name if branch else None


async def _user_branch_from_session(db: AsyncSession, user_id: int) -> int | None:
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(EmployeeBranchSession).where(
            EmployeeBranchSession.employee_id == user_id,
            EmployeeBranchSession.work_date == today,
        )
    )
    session = result.scalar_one_or_none()
    return session.branch_id if session else None


async def _validate_branch_selection(db: AsyncSession, user: User, branch_id: int) -> Branch:
    branch = await db.get(Branch, branch_id)
    if not branch or not branch.is_active:
        raise HTTPException(status_code=400, detail="Invalid branch")

    if user.role == UserRole.EMPLOYEE.value:
        if not await employee_can_use_branch(db, user.id, branch_id):
            raise HTTPException(status_code=403, detail="You are not assigned to this branch")

    return branch


def _user_response(user: User, branch_id: int | None, branch_name: str | None) -> UserResponse:
    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        current_branch_id=branch_id,
        current_branch_name=branch_name,
    )


def _branch_response(branch: Branch) -> BranchResponse:
    return BranchResponse(
        id=branch.id,
        name=branch.name,
        code=branch.code,
        price_per_photo=branch.price_per_photo,
        commission_per_photo=branch.commission_per_photo,
        commission_after_target_per_photo=branch.commission_after_target_per_photo,
        is_active=branch.is_active,
        created_at=branch.created_at,
        updated_at=branch.updated_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    access = create_access_token(str(user.id), user.role)
    refresh = create_refresh_token(str(user.id))
    await log_action(
        db,
        user_id=user.id,
        action="login",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/my-branches", response_model=list[BranchResponse])
async def my_branches(
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.EMPLOYEE.value:
        branches = await get_employee_branches(db, current_user.id)
    else:
        branches = await get_active_branches(db)
    return [_branch_response(b) for b in branches]


@router.post("/select-branch", response_model=TokenResponse)
async def select_branch(
    payload: SelectBranchRequest,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.EMPLOYEE, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    branch = await _validate_branch_selection(db, current_user, payload.branch_id)
    await record_branch_session(db, current_user.id, branch.id)
    extra = {"branch_id": branch.id}
    await log_action(
        db,
        user_id=current_user.id,
        action="select_branch",
        entity_type="branch",
        entity_id=branch.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(
        access_token=create_access_token(str(current_user.id), current_user.role, extra=extra),
        refresh_token=create_refresh_token(str(current_user.id)),
        branch_id=branch.id,
        branch_name=branch.name,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = verify_token(payload.refresh_token, "refresh")
    if not data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = data.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    branch_id = None
    extra = None
    if user.role in (UserRole.EMPLOYEE.value, UserRole.MANAGER.value):
        branch_id = await _user_branch_from_session(db, user.id)
        if branch_id:
            extra = {"branch_id": branch_id}

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role, extra=extra),
        refresh_token=create_refresh_token(str(user.id)),
        branch_id=branch_id,
        branch_name=await _branch_name(db, branch_id),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await log_action(
        db,
        user_id=current_user.id,
        action="logout",
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    branch_id = getattr(request.state, "branch_id", None)
    if branch_id is None and current_user.role in (UserRole.EMPLOYEE.value, UserRole.MANAGER.value):
        branch_id = await _user_branch_from_session(db, current_user.id)
    return _user_response(current_user, branch_id, await _branch_name(db, branch_id))


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode(
            {"sub": str(user.id), "type": "reset", "exp": expire},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        if settings.debug:
            print(f"Password reset link for {user.email}: {reset_url}")
    return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    data = verify_token(payload.token, "reset")
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user_id = data.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    await log_action(db, user_id=user.id, action="reset_password", entity_type="user", entity_id=user.id)
    return MessageResponse(message="Password reset successfully")
