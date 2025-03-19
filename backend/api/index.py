from app.main import app

# This file is kept for compatibility with older deployments
# but is not needed for Render deployments, which use app.main:app directly

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005) 