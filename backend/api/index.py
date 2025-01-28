from mangum import Mangum
from app.main import app

# Vercel serverless function handler
handler = Mangum(app, lifespan="off")

# Make it work with Vercel
def main(event, context):
    return handler(event, context) 