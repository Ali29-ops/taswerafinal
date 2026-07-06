"""Branch management routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.branch import Branch
from app.models.employee_branch import EmployeeBranch, EmployeeBranchSession
from app.models.user import User
from app.schemas import BranchCreate, BranchEmployeesUpdate, BranchResponse, BranchUpdate, MessageResponse
from app.services.audit import log_action
from app.services.branches import get_active_branches

router = APIRouter(prefix="/branches", tags=["Branches"])


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


@router.get("/public", response_model=list[BranchResponse])
async def list_public_branches(db: AsyncSession = Depends(get_db)):
    """Active branches for login page (no auth required)."""
    branches = await get_active_branches(db)
    return [_branch_response(b) for b in branches]


@router.get("", response_model=list[BranchResponse])
async def list_branches(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Branch).order_by(Branch.name))
    return [_branch_response(b) for b in result.scalars().all()]


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    payload: BranchCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Branch).where(Branch.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Branch name already exists")

    branch = Branch(
        name=payload.name,
        code=payload.code,
        price_per_photo=payload.price_per_photo,
        commission_per_photo=payload.commission_per_photo,
        commission_after_target_per_photo=payload.commission_after_target_per_photo,
        is_active=payload.is_active,
    )
    db.add(branch)
    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="create_branch",
        entity_type="branch",
        entity_id=branch.id,
        ip_address=request.client.host if request.client else None,
    )
    return _branch_response(branch)


@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    branch = await db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != branch.name:
        existing = await db.execute(select(Branch).where(Branch.name == data["name"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Branch name already exists")

    for key, value in data.items():
        setattr(branch, key, value)

    await log_action(
        db,
        user_id=current_user.id,
        action="update_branch",
        entity_type="branch",
        entity_id=branch.id,
        ip_address=request.client.host if request.client else None,
    )
    return _branch_response(branch)


@router.delete("/{branch_id}", response_model=MessageResponse)
async def delete_branch(
    branch_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    branch = await db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    await db.delete(branch)
    await log_action(
        db,
        user_id=current_user.id,
        action="delete_branch",
        entity_type="branch",
        entity_id=branch_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Branch deleted")


@router.get("/{branch_id}/employees", response_model=list[int])
async def list_branch_employees(
    branch_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    branch = await db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    result = await db.execute(select(EmployeeBranch.employee_id).where(EmployeeBranch.branch_id == branch_id))
    return list(result.scalars().all())


@router.put("/{branch_id}/employees", response_model=MessageResponse)
async def set_branch_employees(
    branch_id: int,
    payload: BranchEmployeesUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    branch = await db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    employee_ids = payload.employee_ids
    for emp_id in employee_ids:
        emp = await db.get(User, emp_id)
        if not emp or emp.role != UserRole.EMPLOYEE.value:
            raise HTTPException(status_code=400, detail=f"Invalid employee id: {emp_id}")

    existing = await db.execute(select(EmployeeBranch).where(EmployeeBranch.branch_id == branch_id))
    for link in existing.scalars().all():
        await db.delete(link)

    for emp_id in employee_ids:
        db.add(EmployeeBranch(employee_id=emp_id, branch_id=branch_id))

    await log_action(
        db,
        user_id=current_user.id,
        action="set_branch_employees",
        entity_type="branch",
        entity_id=branch_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Branch employees updated")
