mkdir -p backend
cd backend

# Create a virtual environment because global dependencies are for the brave
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies (and hope FastAPI plays nice with your Python version)
pip install fastapi uvicorn anthropic python-dotenv

# Create a .env file for your Anthropic API key