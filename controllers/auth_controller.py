from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.user import User
from middlewares.auth import generate_token

async def register(username: str, email: str, password: str, db: Session):
    try:
        if not username or not email or not password:
            raise HTTPException(status_code=400, detail='All fields are required')

        existing_user = db.query(User).filter(
            or_(User.email == email, User.username == username)
        ).first()

        if existing_user:
            raise HTTPException(status_code=409, detail='User already exists')

        user = User(username=username, email=email, password=password)
        db.add(user)
        db.commit()
        db.refresh(user)

        token = generate_token(user.id)

        return {
            'message': 'User created successfully',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email
            },
            'token': token
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f'Register error: {error}')
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal server error')

async def login(email: str, password: str, db: Session):
    try:
        if not email or not password:
            raise HTTPException(status_code=400, detail='Email and password are required')

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail='Invalid credentials')

        is_valid_password = user.validate_password(password)
        if not is_valid_password:
            raise HTTPException(status_code=401, detail='Invalid credentials')

        token = generate_token(user.id)

        return {
            'message': 'Login successful',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email
            },
            'token': token
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f'Login error: {error}')
        raise HTTPException(status_code=500, detail='Internal server error')

async def get_profile(user: User):
    try:
        return {
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'createdAt': user.createdAt.isoformat()
            }
        }
    except Exception as error:
        print(f'Profile error: {error}')
        raise HTTPException(status_code=500, detail='Internal server error')
