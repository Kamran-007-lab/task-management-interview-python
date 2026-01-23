import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from config.database import Base

class StatusEnum(str, enum.Enum):
    pending = 'pending'
    in_progress = 'in_progress'
    completed = 'completed'

class PriorityEnum(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending, nullable=False)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.medium, nullable=False)
    dueDate = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)
    userId = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index('ix_tasks_userid', 'userId'),
        Index('ix_tasks_status', 'status'),
        Index('ix_tasks_priority', 'priority'),
    )
