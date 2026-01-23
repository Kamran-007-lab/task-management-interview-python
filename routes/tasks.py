from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from config.database import get_db
from controllers.task_controller import (
    create_task,
    get_tasks,
    get_task,
    update_task,
    complete_task,
    delete_task
)
from middlewares.auth import authenticate_token
from models.user import User

router = APIRouter()

# Request models
class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    dueDate: Optional[str] = None

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    dueDate: Optional[str] = None

# Task CRUD operations
@router.post('/')
async def create_new_task(
    request: CreateTaskRequest,
    user: User = Depends(authenticate_token),
    db: Session = Depends(get_db)
):
    return await create_task(
        request.title,
        request.description,
        request.priority,
        request.dueDate,
        user,
        db
    )

@router.get('/')
async def get_all_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    user: User = Depends(authenticate_token),
    db: Session = Depends(get_db)
):
    return await get_tasks(status, priority, page, limit, user, db)

@router.get('/{id}')
async def get_task_by_id(
    id: str,
    user: User = Depends(authenticate_token),
    db: Session = Depends(get_db)
):
    return await get_task(id, user, db)

@router.put('/{id}')
async def update_task_by_id(
    id: str,
    request: UpdateTaskRequest,
    user: User = Depends(authenticate_token),
    db: Session = Depends(get_db)
):
    return await update_task(
        id,
        request.title,
        request.description,
        request.priority,
        request.status,
        request.dueDate,
        user,
        db
    )

@router.delete('/{id}')
async def delete_task_by_id(
    id: str,
    user: User = Depends(authenticate_token),
    db: Session = Depends(get_db)
):
    return await delete_task(id, user, db)

# Task completion endpoint
@router.post('/{id}/complete')
async def complete_task_by_id(
    id: str,
    user: User = Depends(authenticate_token),
    db: Session = Depends(get_db)
):
    return await complete_task(id, user, db)
