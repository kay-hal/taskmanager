from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import os
import logging
from dotenv import load_dotenv
from . import models
from .database import get_db, DatabaseManager, engine
from .task_prioritizer import TaskPrioritizer
import sys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log runtime information
logger.info(f"Starting application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
logger.info(f"RENDER environment variable: {os.getenv('RENDER')}")

# Check for required environment variables
required_variables = ['DATABASE_URL', 'ADMIN_TOKEN', 'ANTHROPIC_API_KEY']
missing_variables = [var for var in required_variables if not os.getenv(var)]
if missing_variables:
    logger.warning(f"Missing required environment variables: {', '.join(missing_variables)}")

# Get admin token
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
if not ADMIN_TOKEN:
    logger.warning("ADMIN_TOKEN not set in environment - admin endpoints will be unusable")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    # Log environment variables (names only)
    logger.info("Environment variables (names only):")
    env_vars = sorted(os.environ.keys())
    logger.info(f"  Found {len(env_vars)} environment variables")
    for key in env_vars:
        # Indicate which critical variables are present (without revealing values)
        if key in required_variables:
            logger.info(f"  ✓ {key} (required)")
        else:
            logger.info(f"  {key}")
    
    # Check database connection
    try:
        db_url = str(engine.url)
        if '@' in db_url:
            # Redact sensitive info
            parts = db_url.split('@')
            redacted_url = f"{parts[0].split('://')[0]}://*****:*****@{parts[1]}"
            logger.info(f"Database URL: {redacted_url}")
        
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            logger.info(f"Database connection test: {result[0] == 1}")
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")

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

@app.post("/api/priorities/refresh")
async def refresh_priorities(db: Session = Depends(get_db)):
    """Refresh task priorities using existing rules without changing them."""
    db_manager = DatabaseManager(db)
    tasks = db_manager.get_all_tasks()
    
    prioritizer = TaskPrioritizer(os.getenv("ANTHROPIC_API_KEY"))
    prioritized_tasks = prioritizer.prioritize_tasks(tasks, db_manager.priority_rules)
    db_manager.update_task_priorities({t.id: t.priority for t in prioritized_tasks})
    
    return {"message": "Task priorities refreshed successfully"}

@app.put("/api/tasks/{task_id}/timer")
async def update_task_timer(task_id: int, timer_update: models.TimerUpdate, db: Session = Depends(get_db)):
    db_manager = DatabaseManager(db)
    updated_task = db_manager.update_task_timer(task_id, timer_update.status, timer_update.time)
    return updated_task

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task_update: models.TaskUpdate, db: Session = Depends(get_db)):
    """Update a task's description."""
    db_manager = DatabaseManager(db)
    updated_task = db_manager.update_task_description(task_id, task_update.description)
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