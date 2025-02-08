import asyncio
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from app.bot.listener import start_bot_listener
from app.core.database import connect_to_db, close_db_connection, get_database
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as user_router

# Load environment variables from .env file
load_dotenv()

# Accessing configurations
MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # Default fallback
API_PORT = int(os.getenv("API_PORT", 8000))   # Default fallback
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Get WEBHOOK_URL here

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Log level(INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Log format
)

# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB and start bot listener
    await connect_to_db()
    logging.info("Connected to database.")
    bot_task = asyncio.create_task(start_bot_listener(webhook_url=WEBHOOK_URL)) # Start bot listener
    logging.info("Telegram bot listener started.")
    yield
    # Shutdown: Close DB connection and stop bot listener
    await close_db_connection()
    logging.info("Database connection closed.")
    bot_task.cancel()
    logging.info("Telegram bot listener stopped.")

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
    return {"status": "running - minimal app"}

# Test database connection route
@app.get("/test-db")
async def test_database():
    try:
        from app.core.database import get_database
        db = get_database()
        sample_document = await db["users"].find_one()
        if sample_document:
            sample_document.pop("_id", None)
            return {"status": "success", "data": sample_document}
        else:
            return {"status": "success", "message": "No documents found in 'users' collection."}
    except Exception as e:
        logging.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)