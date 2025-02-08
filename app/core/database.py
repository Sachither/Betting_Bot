import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Database client (to be shared across the application)
db_client = None

# Access the MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/betting_bot")

async def connect_to_db():
    """
    Establish a connection to the MongoDB database.

    This function initializes the global `db_client` with an asynchronous Motor client.
    It logs the status of the connection and handles errors gracefully.
    """
    global db_client
    try:
        # initialize the Motor client
        logging.info("Connecting to MongoDB database...")
        db_client = AsyncIOMotorClient(MONGO_URI)
        
        # Check connection by running a simple command
        await db_client.admin.command("ping")
        logging.info("Successfully connected to MongoDB database.")
    except Exception as e:
        logging.error(f"An error occurred while connecting to MongoDB database: {e}")
        raise

async def close_db_connection():
    """
    Close the connection to the MongoDB database.

    This function ensures that the `db_client` connection is properly closed during application shutdown.
    """
    global db_client
    if db_client:
        logging.info("Closing connection to MongoDB database...")
        db_client.close()
        logging.info("MongoDB database connection closed.")
        
def get_database():
    """
    Get a reference to the betting bot database.

    This function provides access to the main betting bot database,
    allowing other modules to perform CRUD operations.

    Returns:
        Database: A reference to the MongoDB database.
    """
    global db_client
    if not db_client:
        raise RuntimeError("Database client is not initialized. Call `connect_to_db` first.")
    return db_client.get_default_database() # Defaults to the database name in MONGO_URI