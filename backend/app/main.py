from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import os
import logging
from dotenv import load_dotenv
from . import models
from .database import get_db, DatabaseManager
from .task_prioritizer import TaskPrioritizer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get admin token
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
if not ADMIN_TOKEN:
    raise ValueError("ADMIN_TOKEN must be set in .env file")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=True)

async def verify_admin_token(api_key: str = Security(api_key_header)):
    if api_key != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return api_key

# Routes
@app.get("/")
async def root():
    return {"message": "Task Manager API is running"}

@app.get("/api/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    db_manager = DatabaseManager(db)
    return db_manager.get_all_tasks()

@app.post("/api/tasks")
async def create_task(task: models.TaskCreate, db: Session = Depends(get_db)):
    db_manager = DatabaseManager(db)
    new_task = db_manager.add_task(task.description)
    tasks = db_manager.get_all_tasks()
    
    # Prioritize tasks
    prioritizer = TaskPrioritizer(os.getenv("ANTHROPIC_API_KEY"))
    prioritized_tasks = prioritizer.prioritize_tasks(tasks, db_manager.priority_rules)
    db_manager.update_task_priorities({t.id: t.priority for t in prioritized_tasks})
    
    return new_task

@app.post("/api/priorities")
async def update_priorities(rules: models.PriorityRules, db: Session = Depends(get_db)):
    db_manager = DatabaseManager(db)
    db_manager.priority_rules = [rules.rules]
    tasks = db_manager.get_all_tasks()
    
    prioritizer = TaskPrioritizer(os.getenv("ANTHROPIC_API_KEY"))
    prioritized_tasks = prioritizer.prioritize_tasks(tasks, db_manager.priority_rules)
    db_manager.update_task_priorities({t.id: t.priority for t in prioritized_tasks})
    
    return {"message": "Priorities updated successfully"}

@app.put("/api/tasks/{task_id}/timer")
async def update_task_timer(task_id: int, timer_update: models.TimerUpdate, db: Session = Depends(get_db)):
    db_manager = DatabaseManager(db)
    updated_task = db_manager.update_task_timer(task_id, timer_update.status, timer_update.time)
    return updated_task

@app.delete("/api/admin/tasks")
async def delete_all_tasks(token: str = Depends(verify_admin_token), db: Session = Depends(get_db)):
    try:
        db_manager = DatabaseManager(db)
        db_manager.delete_all_tasks()
        return {"message": "All tasks deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting tasks")