import logging
from fastapi import APIRouter, HTTPException
from app.core.database import get_database

# Create a router instance for managing user-related routes
router = APIRouter()

@router.get("/users", tags=["Users"])
async def get_all_users():
    """
    Fetch all users from the database.
    This endpoint retrieves all documents from the 'users' collection and returns them as a list.
    """
    try:
        db = get_database()  # Get the database instance
        user_collection = db["users"]  # Get the 'users' collection
        
        users = await user_collection.find().to_list(100)
        for user in users:
            user.pop("_id", None)  # Remove sensitive data like _id
        
        return {"users": users}
    except Exception as e:
        logging.error(f"Error while fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users.")