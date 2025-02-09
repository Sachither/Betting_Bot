import asyncio
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.bot.listener import start_bot_listener
from app.core.database import connect_to_db, close_db_connection, get_database
from app.api.routes import router as user_router

# Set Proactor Event Loop on Windows for compatibility with Playwright
if os.name == "nt":  # Check if the system is Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables from .env file
load_dotenv()

# Accessing configurations
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # Default fallback
API_PORT = int(os.getenv("API_PORT", 8000))    # Default fallback
WEBHOOK_URL = os.getenv("WEBHOOK_URL")         # Get WEBHOOK_URL from environment

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Log level(INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log format
)

# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application lifecycle events: startup and shutdown.
    """
    try:
        # Startup: Connect to the database
        await connect_to_db()
        logging.info("✅ Connected to MongoDB.")

        # Start the Telegram bot listener
        bot_task = asyncio.create_task(start_bot_listener(webhook_url=WEBHOOK_URL))
        logging.info("✅ Telegram bot listener started.")

        yield  # Application runs here

    except Exception as e:
        logging.error(f"❌ Error during application startup: {e}")
        raise

    finally:
        # Shutdown: Close database connection and stop bot listener
        await close_db_connection()
        logging.info("✅ MongoDB connection closed.")
        bot_task.cancel()
        logging.info("✅ Telegram bot listener stopped.")

# Initialize FastAPI application
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (update for production!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include user routes
app.include_router(user_router, prefix="/api", tags=["Users"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the application is running.
    """
    return {"status": "running"}

# Test database connection route
@app.get("/test-db")
async def test_database():
    """
    Test the database connection by fetching a sample document.
    """
    try:
        db = get_database()
        sample_document = await db["users"].find_one()
        if sample_document:
            sample_document.pop("_id", None)  # Remove sensitive fields
            return {"status": "success", "data": sample_document}
        else:
            return {"status": "success", "message": "No documents found in 'users' collection."}
    except Exception as e:
        logging.error(f"❌ Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")

# Entry point for the application
if __name__ == "__main__":
    # Ensure compatibility with Playwright on Windows
    if os.name == "nt":  # Check if the system is Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Run the FastAPI application
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
