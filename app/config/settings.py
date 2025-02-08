import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Settings:
    """
    Application settings class.

    This class provides access to the application settings defined in environment variables.
    """
    # MongoDB URI
    MONGO_URI = os.getenv("MONGO_URI")
    # Telegram bot token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    # Other settings......