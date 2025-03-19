import sys
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
logger.info("Loading environment variables...")
load_dotenv()

# Check for DATABASE_URL
db_url = os.environ.get('DATABASE_URL')
if db_url:
    # Redact for logging
    redacted = db_url
    if '@' in db_url:
        parts = db_url.split('@')
        redacted = f"{parts[0].split('://')[0]}://*****:*****@{parts[1]}"
    logger.info(f"Using database: {redacted}")
else:
    logger.info("No DATABASE_URL found, will use SQLite default")

# Import database components
try:
    logger.info("Initializing database...")
    from app.database import engine
    from sqlalchemy import inspect, text
    
    # Import models - explicitly importing them ensures they're registered with SQLAlchemy
    from app.models import TaskModel, PriorityRuleModel
    
    # Get Base class - this is needed to create the tables
    from app.database import Base
    
    # Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify by getting table names
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Database tables: {tables}")
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        if result and result[0] == 1:
            logger.info("✅ Database connection successful")
        else:
            logger.warning("⚠️ Database connection test returned unexpected result")
    
    logger.info("✅ Database initialization complete")
    
except Exception as e:
    logger.error(f"❌ Error initializing database: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

if __name__ == "__main__":
    # Already executed above
    pass 