# Database Scripts

This directory contains scripts for database management.

## init_db.py

This script initializes the database tables for the application. It:

1. Creates the `tasks` and `priority_rules` tables if they don't exist
2. Verifies database connection
3. Logs database information

### Usage

```bash
# From project root
python backend/scripts/init_db.py

# From scripts directory
cd backend/scripts
python init_db.py
```

### Environment Variables

The script uses the following environment variables:

- `DATABASE_URL`: Connection string for the database
  - For PostgreSQL: `postgresql://user:password@host/dbname`
  - If not provided, defaults to SQLite (`sqlite:///./tasks.db`)
- `RENDER`: Set to "true" if running on Render

### Troubleshooting

If you encounter errors:

1. Check that `DATABASE_URL` is correctly set
2. Ensure the database user has privileges to create tables
3. Check logs for specific error messages
4. Make sure required Python packages are installed (`pip install -r ../requirements.txt`)

## deploy_render.sh

Script for deploying to Render. Uses `render deploy` to deploy the application. 