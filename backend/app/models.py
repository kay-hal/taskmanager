from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from .database import Base
from .enums import TaskStatus

# SQLAlchemy Models
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    priority = Column(Integer)
    status = Column(SQLEnum(TaskStatus))
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_time = Column(Integer, default=0)

class PriorityRuleModel(Base):
    __tablename__ = "priority_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule = Column(String)

# Pydantic Models
class Task(BaseModel):
    id: int
    description: str
    priority: int
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_time: int

    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    description: str

class TaskUpdate(BaseModel):
    description: str

class PriorityRules(BaseModel):
    rules: str

class TimerUpdate(BaseModel):
    status: TaskStatus
    time: int

class TaskPriority(BaseModel):
    task_id: int = Field(..., description="The ID of the task")
    priority: int = Field(..., ge=1, description="Priority score 1 is highest priority and ascending order")
    explanation: str = Field(..., description="Explanation for the priority assignment")

class TaskPriorities(BaseModel):
    tasks: List[TaskPriority] 