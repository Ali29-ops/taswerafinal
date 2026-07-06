"""Manager-employee assignment routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.core.roles import UserRole
from app.database import get_db
from app.models.manager_employee import ManagerEmployee
from app.models.user import User
from app.schemas import ManagerAssignmentCreate, ManagerAssignmentResponse, ManagerAssignmentUpdate, MessageResponse
from app.services.audit import log_action

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("", response_model=list[ManagerAssignmentResponse])
async def list_assignments(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ManagerEmployee)
    if current_user.role == UserRole.MANAGER.value:
        stmt = stmt.where(ManagerEmployee.manager_id == current_user.id)
    result = await db.execute(stmt)
    assignments = result.scalars().all()
    responses = []
    for a in assignments:
        mgr = await db.get(User, a.manager_id)
        emp = await db.get(User, a.employee_id)
        responses.append(
            ManagerAssignmentResponse(
                id=a.id,
                manager_id=a.manager_id,
                employee_id=a.employee_id,
                created_at=a.created_at,
                manager_name=f"{mgr.first_name} {mgr.last_name}" if mgr else None,
                employee_name=f"{emp.first_name} {emp.last_name}" if emp else None,
            )
        )
    return responses


@router.post("", response_model=ManagerAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: ManagerAssignmentCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    manager, employee = await _validate_assignment(db, payload.manager_id, payload.employee_id)
    assignment = ManagerEmployee(manager_id=payload.manager_id, employee_id=payload.employee_id)
    db.add(assignment)
    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="assign_employee",
        entity_type="manager_employee",
        entity_id=assignment.id,
        ip_address=request.client.host if request.client else None,
    )
    return ManagerAssignmentResponse(
        id=assignment.id,
        manager_id=assignment.manager_id,
        employee_id=assignment.employee_id,
        created_at=assignment.created_at,
        manager_name=f"{manager.first_name} {manager.last_name}",
        employee_name=f"{employee.first_name} {employee.last_name}",
    )


async def _validate_assignment(
    db: AsyncSession, manager_id: int, employee_id: int, exclude_id: int | None = None
) -> tuple[User, User]:
    manager = await db.get(User, manager_id)
    employee = await db.get(User, employee_id)
    if not manager or manager.role != UserRole.MANAGER.value:
        raise HTTPException(status_code=400, detail="Invalid manager")
    if not employee or employee.role != UserRole.EMPLOYEE.value:
        raise HTTPException(status_code=400, detail="Invalid employee")

    stmt = select(ManagerEmployee).where(
        ManagerEmployee.manager_id == manager_id,
        ManagerEmployee.employee_id == employee_id,
    )
    if exclude_id is not None:
        stmt = stmt.where(ManagerEmployee.id != exclude_id)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Assignment already exists")
    return manager, employee


@router.patch("/{assignment_id}", response_model=ManagerAssignmentResponse)
async def update_assignment(
    assignment_id: int,
    payload: ManagerAssignmentUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.get(ManagerEmployee, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No changes provided")

    manager_id = data.get("manager_id", assignment.manager_id)
    employee_id = data.get("employee_id", assignment.employee_id)
    manager, employee = await _validate_assignment(db, manager_id, employee_id, exclude_id=assignment.id)

    assignment.manager_id = manager_id
    assignment.employee_id = employee_id
    await db.flush()
    await log_action(
        db,
        user_id=current_user.id,
        action="update_assignment",
        entity_type="manager_employee",
        entity_id=assignment.id,
        ip_address=request.client.host if request.client else None,
    )
    return ManagerAssignmentResponse(
        id=assignment.id,
        manager_id=assignment.manager_id,
        employee_id=assignment.employee_id,
        created_at=assignment.created_at,
        manager_name=f"{manager.first_name} {manager.last_name}",
        employee_name=f"{employee.first_name} {employee.last_name}",
    )


@router.delete("/{assignment_id}", response_model=MessageResponse)
async def delete_assignment(
    assignment_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.get(ManagerEmployee, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await db.delete(assignment)
    await log_action(
        db,
        user_id=current_user.id,
        action="unassign_employee",
        entity_type="manager_employee",
        entity_id=assignment_id,
        ip_address=request.client.host if request.client else None,
    )
    return MessageResponse(message="Assignment removed")
