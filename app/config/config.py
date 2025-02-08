import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration values
API_HOST = os.getenv("API_HOST", "127.0.0.1")
MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_PORT = int(os.getenv("API_PORT", 8000))  # Default fallback

