from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from config.database import get_db
from controllers.auth_controller import register, login, get_profile
from middlewares.auth import authenticate_token
from models.user import User

router = APIRouter()

# Request models
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Public routes
@router.post('/register')
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    return await register(request.username, request.email, request.password, db)

@router.post('/login')
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    return await login(request.email, request.password, db)

# Protected routes
@router.get('/profile')
async def get_user_profile(user: User = Depends(authenticate_token)):
    return await get_profile(user)
