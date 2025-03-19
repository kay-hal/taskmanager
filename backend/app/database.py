import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime
import logging
from . import models
from .enums import TaskStatus
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Check if running on Render
IS_RENDER = os.environ.get('RENDER', False)

if IS_RENDER:
    # Use Render PostgreSQL
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    logger.info(f"Using Render PostgreSQL database (URL redacted)")
else:
    # Use SQLite for local development
    DATABASE_URL = "sqlite:///./tasks.db"
    logger.info(f"Using SQLite database: {DATABASE_URL}")

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseManager:
    def __init__(self, session: Session):
        self.session = session
        self._priority_rules = []

    def get_all_tasks(self):
        logger.debug("Retrieving all tasks")
        return self.session.query(models.TaskModel).order_by(
            models.TaskModel.priority.desc(),
            models.TaskModel.created_at
        ).all()

    def add_task(self, description: str):
        logger.info(f"Adding new task with description: {description}")
        db_task = models.TaskModel(
            description=description,
            priority=len(self.get_all_tasks()) + 1,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            total_time=0
        )
        self.session.add(db_task)
        self.session.commit()
        self.session.refresh(db_task)
        return db_task

    def update_task_description(self, task_id: int, description: str):
        """Update the description of a task."""
        logger.info(f"Updating description for task {task_id} to: {description}")
        db_task = self.session.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()
        if not db_task:
            logger.error(f"Task {task_id} not found")
            raise HTTPException(status_code=404, detail="Task not found")
        
        db_task.description = description
        self.session.commit()
        self.session.refresh(db_task)
        return db_task

    def update_task_timer(self, task_id: int, status: TaskStatus, time: int):
        logger.info(f"Updating timer for task {task_id} - Status: {status}, Time: {time}")
        db_task = self.session.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()
        if not db_task:
            logger.error(f"Task {task_id} not found")
            raise HTTPException(status_code=404, detail="Task not found")
        
        db_task.status = status
        db_task.total_time = time
        
        if status == TaskStatus.ACTIVE and not db_task.started_at:
            db_task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            db_task.completed_at = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_task)
        return db_task

    def update_task_priorities(self, task_priorities: dict):
        for task_id, priority in task_priorities.items():
            db_task = self.session.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()
            if db_task:
                db_task.priority = priority
        self.session.commit()

    def delete_all_tasks(self):
        self.session.query(models.TaskModel).delete()
        self.session.commit()

    @property
    def priority_rules(self) -> list[str]:
        rules = self.session.query(models.PriorityRuleModel).all()
        return [rule.rule for rule in rules]

    @priority_rules.setter
    def priority_rules(self, rules: list[str]):
        self.session.query(models.PriorityRuleModel).delete()
        for rule in rules:
            db_rule = models.PriorityRuleModel(rule=rule)
            self.session.add(db_rule)
        self.session.commit() 