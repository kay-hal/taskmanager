import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Log environment for debugging
logger.info("Initialization script starting")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info("Environment variables (keys only):")
for key in sorted(os.environ.keys()):
    logger.info(f"  {key}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check if running on Render (multiple ways to detect)
IS_RENDER = (
    os.environ.get('RENDER', '').lower() in ('1', 'true', 't', 'yes', 'y') or
    'render.com' in os.environ.get('HOSTNAME', '')
)
logger.info(f"Running on Render: {IS_RENDER}")

# Ensure DATABASE_URL is set
db_url = os.environ.get('DATABASE_URL')
if db_url:
    logger.info("Found DATABASE_URL in environment")
    # Redact sensitive part for logging
    if '@' in db_url:
        parts = db_url.split('@')
        redacted = f"{parts[0].split('://')[0]}://*****:*****@{parts[1]}"
        logger.info(f"Database URL: {redacted}")
else:
    logger.warning("DATABASE_URL not found in environment")
    
    if IS_RENDER:
        logger.critical("DATABASE_URL environment variable is required for Render deployment")
        sys.exit(1)
    
    # Load production environment variables
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.production')
    if os.path.exists(env_file):
        logger.info(f"Loading environment from: {env_file}")
        load_dotenv(env_file, override=True)
        if 'DATABASE_URL' in os.environ:
            logger.info("DATABASE_URL loaded from .env.production")
        else:
            logger.warning("DATABASE_URL not found in .env.production")

# Verify DATABASE_URL is now set
if not os.environ.get('DATABASE_URL'):
    logger.critical("DATABASE_URL is still not set after all attempts!")
    sys.exit(1)

# Import these after environment variables are loaded
logger.info("Importing database modules...")
from app.database import engine
from app.db_base import Base
from app.models import TaskModel, PriorityRuleModel
from sqlalchemy import text, inspect

def init_database():
    try:
        logger.info("Starting database initialization...")
        
        # Log database connection info (without credentials)
        db_url = str(engine.url)
        if '@' in db_url:
            # Redact sensitive information
            parts = db_url.split('@')
            redacted_url = f"{parts[0].split('://')[0]}://*****@{parts[1]}"
            logger.info(f"Database URL: {redacted_url}")
        else:
            logger.info(f"Database type: {engine.url.drivername}")
        
        # Check for existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables before init: {existing_tables}")
        
        # Drop tables if they exist (force recreate)
        if 'tasks' in existing_tables or 'priority_rules' in existing_tables:
            logger.info("Dropping existing tables...")
            Base.metadata.drop_all(bind=engine, tables=[TaskModel.__table__, PriorityRuleModel.__table__])
            logger.info("Existing tables dropped.")
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables after creation: {tables}")
        
        required_tables = ["tasks", "priority_rules"]
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            logger.error(f"Failed to create tables: {missing_tables}")
            raise ValueError(f"Tables not created: {missing_tables}")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                logger.info("✅ Database connection verified")
            else:
                logger.warning("Connection test returned unexpected result")
                
        logger.info("✅ Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 