from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import anthropic
import os
from collections import defaultdict
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

class TaskCreate(BaseModel):
    description: str

class PriorityRules(BaseModel):
    rules: str

class TimerUpdate(BaseModel):
    status: TaskStatus
    time: int

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

# In-memory database
class Database:
    def __init__(self):
        self.tasks = {}
        self.priority_rules = []
        self.next_id = 1
        logger.info("Database initialized")

    def add_task(self, description: str) -> Task:
        logger.info(f"Adding new task with description: {description}")
        task = Task(
            id=self.next_id,
            description=description,
            priority=len(self.tasks) + 1,  # Default priority
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            total_time=0
        )
        self.tasks[self.next_id] = task
        logger.info(f"Task created with ID: {self.next_id}")
        self.next_id += 1
        return task

    def update_task_timer(self, task_id: int, status: TaskStatus, time: int) -> Task:
        logger.info(f"Updating timer for task {task_id} - Status: {status}, Time: {time}")
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = self.tasks[task_id]
        task.status = status
        task.total_time = time
        
        if status == TaskStatus.ACTIVE and not task.started_at:
            task.started_at = datetime.now()
            logger.info(f"Task {task_id} started at {task.started_at}")
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            logger.info(f"Task {task_id} completed at {task.completed_at}")
            
        return task

    def get_all_tasks(self) -> List[Task]:
        logger.debug("Retrieving all tasks")
        return sorted(self.tasks.values(), key=lambda x: (-x.priority, x.created_at))

db = Database()

# Claude AI integration
def prioritize_tasks_with_claude(tasks: List[Task], rules: List[str]) -> List[Task]:
    logger.info("Starting task prioritization with Claude")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        raise HTTPException(status_code=500, detail="API key not configured")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Define the tool for JSON output
    tools = [{
        "name": "prioritize_tasks",
        "description": "Analyze tasks and assign priority scores based on importance and urgency. Return a structured list of task priorities with explanations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                            "explanation": {"type": "string"}
                        },
                        "required": ["task_id", "priority", "explanation"]
                    }
                }
            },
            "required": ["tasks"]
        }
    }]
    
    # Prepare task descriptions
    task_descriptions = "\n".join([
        f"- Task ID {task.id}: {task.description} (Status: {task.status})"
        for task in tasks if task.status != TaskStatus.COMPLETED
    ])
    
    rules_text = "\n".join([f"- {rule}" for rule in rules]) if rules else "No specific rules provided"
    
    prompt = f"""Analyze these tasks and assign priority scores (1-10, where 10 is highest priority) based on importance and urgency.

Rules to consider:
{rules_text}

Tasks to prioritize:
{task_descriptions}

Use the prioritize_tasks tool to provide the priority scores and explanations."""

    # Get Claude's response with forced tool use
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        tool_choice={"type": "tool", "name": "prioritize_tasks"}
    )
    
    # Extract the tool use response
    tool_calls = [content for content in message.content if content.type == "tool_calls"]
    if tool_calls and tool_calls[0].tool_calls:
        tool_call = tool_calls[0].tool_calls[0]
        priority_data = tool_call.parameters["tasks"]
        
        # Update task priorities
        priority_map = {item["task_id"]: item["priority"] for item in priority_data}
        for task in tasks:
            if task.id in priority_map:
                task.priority = priority_map[task.id]
                logger.debug(f"Priority {priority_map[task.id]} assigned to task {task.id}")
    
    logger.info("Task prioritization completed")
    return tasks

@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    logger.info(f"Received request to create task: {task.description}")
    new_task = db.add_task(task.description)
    tasks = db.get_all_tasks()
    prioritize_tasks_with_claude(tasks, db.priority_rules)
    logger.info(f"Task created successfully with ID: {new_task.id}")
    return new_task

@app.post("/api/priorities")
async def update_priorities(rules: PriorityRules):
    logger.info("Updating priority rules")
    db.priority_rules = [rules.rules]
    tasks = db.get_all_tasks()
    prioritized_tasks = prioritize_tasks_with_claude(tasks, db.priority_rules)
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