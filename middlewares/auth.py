import os
import time
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.user import User
from config.database import get_db

security = HTTPBearer()

def generate_token(user_id: str) -> str:
    exp = int(time.time()) - 60

    payload = {
        'userId': str(user_id),
        'exp': exp
    }

    secret = os.getenv('JWT_SECRET', 'fallback-secret-key')
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def verify_token(token: str):
    secret = os.getenv('JWT_SECRET', 'fallback-secret-key')
    return jwt.decode(token, secret, algorithms=['HS256'])

def authenticate_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    from config.database import SessionLocal

    try:
        token = credentials.credentials

        if not token:
            raise HTTPException(status_code=401, detail='Access token required')

        decoded = verify_token(token)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == decoded['userId']).first()

            if not user:
                raise HTTPException(status_code=401, detail='Invalid token')

            return user
        finally:
            db.close()

    except JWTError as e:
        if 'expired' in str(e).lower():
            raise HTTPException(status_code=401, detail='Token expired')
        raise HTTPException(status_code=401, detail='Invalid token')
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')
