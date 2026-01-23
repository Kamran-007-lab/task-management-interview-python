from models.user import User
from models.task import Task
from config.database import Base, engine

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

__all__ = ['User', 'Task', 'init_db']
