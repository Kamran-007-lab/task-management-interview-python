import asyncio
import json
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user import User
from models.task import Task, StatusEnum, PriorityEnum
from config.redis import get_redis_client
from jobs.email_job import add_email_job

CACHE_KEY = 'incomplete_tasks'
CACHE_EXPIRY = 300

async def create_task(
    title: str,
    description: Optional[str],
    priority: Optional[str],
    due_date: Optional[str],
    user: User,
    db: Session
):
    try:
        if not title:
            raise HTTPException(status_code=400, detail='Title is required')

        task = Task(
            title=title,
            description=description,
            priority=PriorityEnum(priority) if priority else PriorityEnum.medium,
            dueDate=datetime.fromisoformat(due_date) if due_date else None,
            userId=user.id
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        redis_client = get_redis_client()
        redis_client.delete(CACHE_KEY)

        return {
            'message': 'Task created successfully',
            'task': serialize_task(task)
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f'Create task error: {error}')
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal server error')

async def get_tasks(
    status: Optional[str],
    priority: Optional[str],
    page: int,
    limit: int,
    user: User,
    db: Session
):
    try:
        # Build where clause
        filters = [Task.userId == user.id]
        if status:
            filters.append(Task.status == StatusEnum(status))
        if priority:
            filters.append(Task.priority == PriorityEnum(priority))

        # Check cache for incomplete tasks only
        redis_client = get_redis_client()
        if status != 'completed' and not priority:
            cached_tasks = redis_client.get(CACHE_KEY)
            if cached_tasks:
                print('Returning cached tasks')
                return json.loads(cached_tasks)

        offset = (page - 1) * limit
        tasks_query = db.query(Task).filter(*filters)
        total = tasks_query.count()
        tasks = tasks_query.order_by(Task.createdAt.desc()).offset(offset).limit(limit).all()

        result = {
            'tasks': [serialize_task_with_user(task, db) for task in tasks],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'totalPages': (total + limit - 1) // limit
            }
        }

        # Cache incomplete tasks
        if status != 'completed' and not priority:
            redis_client.setex(CACHE_KEY, CACHE_EXPIRY, json.dumps(result, default=str))

        return result
    except HTTPException:
        raise
    except Exception as error:
        print(f'Get tasks error: {error}')
        raise HTTPException(status_code=500, detail='Internal server error')

async def get_task(task_id: str, user: User, db: Session):
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.userId == user.id).first()

        if not task:
            raise HTTPException(status_code=404, detail='Task not found')

        return {'task': serialize_task_with_user(task, db)}
    except HTTPException:
        raise
    except Exception as error:
        print(f'Get task error: {error}')
        raise HTTPException(status_code=500, detail='Internal server error')

async def update_task(
    task_id: str,
    title: Optional[str],
    description: Optional[str],
    priority: Optional[str],
    status: Optional[str],
    due_date: Optional[str],
    user: User,
    db: Session
):
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.userId == user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail='Task not found')

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = PriorityEnum(priority)
        if status is not None:
            task.status = StatusEnum(status)
        if due_date is not None:
            task.dueDate = datetime.fromisoformat(due_date) if due_date else None

        db.commit()
        db.refresh(task)

        redis_client = get_redis_client()
        redis_client.delete(CACHE_KEY)

        return {
            'message': 'Task updated successfully',
            'task': serialize_task(task)
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f'Update task error: {error}')
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal server error')

async def complete_task(task_id: str, user: User, db: Session):
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.userId == user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail='Task not found')

        if task.status == StatusEnum.completed:
            raise HTTPException(status_code=400, detail='Task already completed')

        task.status = StatusEnum.completed
        db.commit()
        db.refresh(task)

        async def delayed_save():
            await asyncio.sleep(0.01)
            task.completedAt = datetime.now()
            db.commit()

        asyncio.create_task(delayed_save())

        await add_email_job({
            'userId': str(user.id),
            'taskId': str(task_id),
            'taskTitle': task.title,
            'type': 'task_completion'
        })

        return {
            'message': 'Task completed successfully',
            'task': serialize_task(task)
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f'Complete task error: {error}')
        raise HTTPException(status_code=500, detail='Internal server error')

async def delete_task(task_id: str, user: User, db: Session):
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.userId == user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail='Task not found')

        db.delete(task)
        db.commit()

        redis_client = get_redis_client()
        redis_client.delete(CACHE_KEY)

        return {'message': 'Task deleted successfully'}
    except HTTPException:
        raise
    except Exception as error:
        print(f'Delete task error: {error}')
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal server error')

def serialize_task(task: Task):
    return {
        'id': str(task.id),
        'title': task.title,
        'description': task.description,
        'status': task.status.value,
        'priority': task.priority.value,
        'dueDate': task.dueDate.isoformat() if task.dueDate else None,
        'completedAt': task.completedAt.isoformat() if task.completedAt else None,
        'userId': str(task.userId),
        'createdAt': task.createdAt.isoformat(),
        'updatedAt': task.updatedAt.isoformat()
    }

def serialize_task_with_user(task: Task, db: Session):
    user = db.query(User).filter(User.id == task.userId).first()
    task_data = serialize_task(task)
    task_data['user'] = {
        'username': user.username,
        'email': user.email
    }
    return task_data
