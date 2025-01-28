from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import anthropic
import os
from collections import defaultdict
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import secrets

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get admin token from environment variables
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
if not ADMIN_TOKEN:
    raise ValueError("ADMIN_TOKEN must be set in .env file")

class TaskStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

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
        orm_mode = True
        model_config = {'from_attributes': True}

class TaskCreate(BaseModel):
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

class TaskPrioritizer:
    def __init__(self, api_key: str):
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            raise ValueError("API key not configured")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def _build_prompt(self, tasks: List[Task], rules: List[str]) -> str:
        task_descriptions = "\n".join([
            f"- Task ID {task.id}: {task.description} (Status: {task.status}) \n"
            for task in tasks if task.status != TaskStatus.COMPLETED
        ])
        
        rules_text = "\n".join([f"- {rule}" for rule in rules]) if rules else "No specific rules provided"
        
        return f"""here's a list of task descriptions
                \"\"\"
                {task_descriptions}
                \"\"\"

                and here is the prioritization statement about how to prioritize the tasks
                \"\"\"
                {rules_text}
                \"\"\"

                rank the tasks based on the prioritization statement and give me a json list of the specified schema. do not change anything in the task description. only give me the json list and nothing else"""

    def prioritize_tasks(self, tasks: List[Task], rules: List[str]) -> List[Task]:
        self.logger.info("Starting task prioritization with Claude")
        
        prompt = self._build_prompt(tasks, rules)
        self.logger.info(f"Prompt: {prompt}")

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "name": "prioritize_tasks",
                    "description": "rank the tasks based on the prioritization statement strictly ensuring the most important tasks are ranked higher. Return a structured list of task priorities with explanations using the prioritize_tasks tool",
                    "input_schema": TaskPriorities.model_json_schema()
                }],
                tool_choice={"type": "tool", "name": "prioritize_tasks"}
            )

            self.logger.info(f"Message: {message}")
            # Extract and validate the tool use response
            tool_calls = [content for content in message.content if content.type == "tool_use"]
            if not tool_calls:
                self.logger.error("No tool calls found in response")
                return tasks

            tool_call = tool_calls[0]
            if not tool_call.input:
                self.logger.error("No input found in tool call")
                return tasks

            # Validate the response using Pydantic
            priority_data = TaskPriorities(**tool_call.input)
            
            # Update task priorities
            priority_map = {item.task_id: item.priority for item in priority_data.tasks}
            for task in tasks:
                if task.id in priority_map:
                    task.priority = priority_map[task.id]
                    self.logger.info(f"Priority {priority_map[task.id]} assigned to task {task.id}")

        except Exception as e:
            self.logger.error(f"Error processing priorities: {str(e)}")
            return tasks

        self.logger.info("Task prioritization completed")
        return tasks

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify the allowed origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a test route to verify the server is working
@app.get("/")
async def root():
    return {"message": "Task Manager API is running"}

# Add a test route for tasks
@app.get("/api/tasks")
async def get_tasks():
    tasks = db.get_all_tasks()  # Assuming this is the method to get all tasks
    return tasks  # Return the tasks array directly

# Log startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application")

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy models
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    priority = Column(Integer)
    status = Column(SQLEnum(TaskStatus))
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_time = Column(Integer)

class PriorityRuleModel(Base):
    __tablename__ = "priority_rules"
    
    id = Column(Integer, primary_key=True)
    rule = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

class Database:
    def __init__(self):
        self.session = SessionLocal()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.prioritizer = TaskPrioritizer(api_key)
        self._priority_rules = []  # Initialize empty rules list
        logger.info("Database initialized")

    @property
    def priority_rules(self) -> List[str]:
        # Get rules from database
        rules = self.session.query(PriorityRuleModel).all()
        return [rule.rule for rule in rules]

    @priority_rules.setter
    def priority_rules(self, rules: List[str]):
        # Clear existing rules
        self.session.query(PriorityRuleModel).delete()
        
        # Add new rules
        for rule in rules:
            db_rule = PriorityRuleModel(rule=rule)
            self.session.add(db_rule)
        
        self.session.commit()

    def add_task(self, description: str) -> Task:
        logger.info(f"Adding new task with description: {description}")
        db_task = TaskModel(
            description=description,
            priority=len(self.get_all_tasks()) + 1,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            total_time=0
        )
        self.session.add(db_task)
        self.session.commit()
        self.session.refresh(db_task)
        
        # Convert to Pydantic model
        return Task.model_validate(db_task, from_attributes=True)

    def update_task_timer(self, task_id: int, status: TaskStatus, time: int) -> Task:
        logger.info(f"Updating timer for task {task_id} - Status: {status}, Time: {time}")
        db_task = self.session.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not db_task:
            logger.error(f"Task {task_id} not found")
            raise HTTPException(status_code=404, detail="Task not found")
        
        db_task.status = status
        db_task.total_time = time
        
        if status == TaskStatus.ACTIVE and not db_task.started_at:
            db_task.started_at = datetime.now()
            logger.info(f"Task {task_id} started at {db_task.started_at}")
        elif status == TaskStatus.COMPLETED:
            db_task.completed_at = datetime.now()
            logger.info(f"Task {task_id} completed at {db_task.completed_at}")
        
        self.session.commit()
        self.session.refresh(db_task)
        return Task.model_validate(db_task, from_attributes=True)

    def get_all_tasks(self) -> List[Task]:
        logger.debug("Retrieving all tasks")
        db_tasks = self.session.query(TaskModel).order_by(
            TaskModel.priority.desc(),
            TaskModel.created_at
        ).all()
        return [Task.model_validate(task, from_attributes=True) for task in db_tasks]

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        # Get the prioritized tasks from Claude
        prioritized_tasks = self.prioritizer.prioritize_tasks(tasks, self.priority_rules)
        
        # Update priorities in the database
        for task in prioritized_tasks:
            db_task = self.session.query(TaskModel).filter(TaskModel.id == task.id).first()
            if db_task:
                db_task.priority = task.priority
        
        self.session.commit()
        return prioritized_tasks

db = Database()

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    logger.info(f"Received request to create task: {task.description}")
    new_task = db.add_task(task.description)
    tasks = db.get_all_tasks()
    db.prioritize_tasks(tasks)
    logger.info(f"Task created successfully with ID: {new_task.id}")
    return new_task

@app.post("/api/priorities")
async def update_priorities(rules: PriorityRules):
    logger.info("Updating priority rules with rules: " + rules.rules)
    db.priority_rules = [rules.rules]
    tasks = db.get_all_tasks()
    prioritized_tasks = db.prioritize_tasks(tasks)
    logger.info("Priorities updated successfully")
    return {"message": "Priorities updated successfully"}

@app.put("/api/tasks/{task_id}/timer")
async def update_task_timer(task_id: int, timer_update: TimerUpdate):
    logger.info(f"Updating timer for task {task_id}")
    updated_task = db.update_task_timer(task_id, timer_update.status, timer_update.time)
    return updated_task

@app.get("/api/tasks")
async def get_tasks():
    logger.info("Retrieving all tasks")
    return db.get_all_tasks()

# Create the security scheme
api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=True)

async def verify_admin_token(api_key: str = Security(api_key_header)):
    print(f"ADMIN_TOKEN: {ADMIN_TOKEN}")
    print(f"api_key: {api_key}")
    if api_key != ADMIN_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin token"
        )
    return api_key

@app.delete("/api/admin/tasks")
async def delete_all_tasks(token: str = Depends(verify_admin_token)):
    try:
        db = SessionLocal()
        db.query(TaskModel).delete()
        db.commit()
        logger.info("All tasks deleted by admin")
        return {"message": "All tasks deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting tasks")
    finally:
        db.close()