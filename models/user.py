import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import bcrypt as bcrypt_lib
from config.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    tasks = relationship("Task", back_populates="user")

    def __init__(self, username, email, password):
        self.id = uuid.uuid4()
        self.username = username
        self.email = email
        salt = bcrypt_lib.gensalt(rounds=10)
        self.password = bcrypt_lib.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        self.createdAt = datetime.now()
        self.updatedAt = datetime.now()

    def validate_password(self, password):
        return bcrypt_lib.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
