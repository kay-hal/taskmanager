import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime
import logging
# Avoid circular import by importing models and enums only in functions where needed
from .enums import TaskStatus
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log all environment variables for debugging (with sensitive info redacted)
logger.info("Environment Variables (names only):")
for key in os.environ.keys():
    logger.info(f"  {key}")

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Check if we're running on Render (various ways to detect)
IS_RENDER = os.environ.get('RENDER', False) or 'render.com' in os.environ.get('HOSTNAME', '')
logger.info(f"Running on Render: {IS_RENDER}")

if not DATABASE_URL:
    if IS_RENDER:
        logger.critical("DATABASE_URL not found in environment but required for Render deployment")
        raise ValueError("DATABASE_URL environment variable is required for Render deployment")
    else:
        # Use SQLite for local development
        DATABASE_URL = "sqlite:///./tasks.db"
        logger.info(f"Using SQLite database: {DATABASE_URL}")

# Redact and log database URL for debugging
if DATABASE_URL:
    redacted_url = DATABASE_URL
    if '@' in redacted_url:
        # Hide sensitive credentials in logs
        parts = redacted_url.split('@')
        protocol_parts = parts[0].split('://')
        if len(protocol_parts) > 1:
            redacted_url = f"{protocol_parts[0]}://****:****@{parts[1]}"
    logger.info(f"Database URL: {redacted_url}")
else:
    logger.critical("No DATABASE_URL could be determined!")

# Configure engine based on database type
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
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
        # Import here to avoid circular imports
        from . import models
        return self.session.query(models.TaskModel).order_by(
            models.TaskModel.priority.desc(),
            models.TaskModel.created_at
        ).all()

    def add_task(self, description: str):
        logger.info(f"Adding new task with description: {description}")
        # Import here to avoid circular imports
        from . import models
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
        # Import here to avoid circular imports
        from . import models
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
        # Import here to avoid circular imports
        from . import models
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
        # Import here to avoid circular imports
        from . import models
        for task_id, priority in task_priorities.items():
            db_task = self.session.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()
            if db_task:
                db_task.priority = priority
        self.session.commit()

    def delete_all_tasks(self):
        # Import here to avoid circular imports
        from . import models
        self.session.query(models.TaskModel).delete()
        self.session.commit()

    @property
    def priority_rules(self) -> list[str]:
        # Import here to avoid circular imports
        from . import models
        rules = self.session.query(models.PriorityRuleModel).all()
        return [rule.rule for rule in rules]

    @priority_rules.setter
    def priority_rules(self, rules: list[str]):
        # Import here to avoid circular imports
        from . import models
        self.session.query(models.PriorityRuleModel).delete()
        for rule in rules:
            db_rule = models.PriorityRuleModel(rule=rule)
            self.session.add(db_rule)
        self.session.commit() 