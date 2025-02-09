"""
This module contains handlers for Telegram bot commands. It focuses on clean
and modular implementation for each command.
"""
import logging
import bcrypt
from telegram import ForceReply, Update
from telegram.ext import ContextTypes

import asyncio

from app.core.database import get_database
from app.core.scraper import validate_sportybet_credentials
from app.core.session_manager import SessionManager
from app.core.utils import delete_password_message_later

session_manager = SessionManager() # Initialize the session manager globally

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command.
    Display a welcome message and offer login or skip options.
    """
    await update.message.reply_text(
        "Welcome to the BetNudge Bot! 🎉\n"
        "I am here to automate your betting experience.\n"
        "What would you like to do?\n"
        "1. /login - Log in to your SportyBet account.\n"
        "2. /skip - Skip login and use limited features."
    )

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /login command.
    Prompt the user to enter their SportyBet login details.
    """
    user_id = update.effective_user.id
    await update.message.reply_text("Please enter your SportyBet phone number")
    context.user_data["awaiting_phone_number"] = True # Set a state to await username
    context.user_data["user_id"] = user_id # Store the user ID for session management
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /help command.
    Displays a list of available commands.
    """
    help_text = """
    I am your Betting Bot. Here are the commands you can use:
    /start - Start the bot and see welcome options.
    /help - Display this help text.
    """
    await update.message.reply_text(help_text)
    
async def text_handler(update, context):
    """
    Handle user input for login credentials.
    Process both username and password and validate them with SportyBet.
    """
    if context.user_data.get('awaiting_phone_number'):
        phone_number = update.message.text.strip()

        if not phone_number.isdigit():
            await update.message.reply_text("Invalid phone number. Please enter digits only.")
            return
        
        # Check if the phone number length is valid
        if len(phone_number) < 10 or len(phone_number) > 11:
            await update.message.reply_text("Invalid phone number. The phone number must be 10 or 11 digits long.")
            return
        
        # Store phone number and ask for password
        context.user_data['phone_number'] = phone_number
        context.user_data['user_id'] = update.effective_user.id  # Store user ID for session management
        context.user_data['awaiting_phone_number'] = False
        context.user_data['awaiting_password'] = True
        await update.message.reply_text(
            "Please enter your password:",
        )
    elif context.user_data.get('awaiting_password'):
        # Capture the message object for deletion
        password_message = update.message
        password = update.message.text.strip()

        if not password:
            await update.message.reply_text("Password cannot be empty. Please try again.")
            return

        # Validate login using Playwright
        phone_number = context.user_data.get('phone_number')
        user_id = context.user_data.get('user_id')  # Get the user ID
        
        loop = asyncio.get_event_loop()
        login_result = await loop.run_in_executor(
            None, 
            validate_sportybet_credentials,
            user_id,
            phone_number,
            password,
            session_manager,
            False
        )

        if login_result["success"]:
            # Save user details in the database
            balance = login_result["balance"]
            db = get_database()

            # Hash the password before saving
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

            # Debug: Log what is being saved
            logging.info(f"Saving user: phone_number={phone_number}, balance={balance}")
            
            # Insert or update user details in MongoDB
            try:
                result = await db["users"].update_one(
                    {"phone_number": phone_number},  # Match on phone number
                    {"$set": {"phone_number": phone_number, "password": hashed_password.decode(), "balance": balance}},
                    upsert=True  # Insert if user doesn't exist
                )
            
                # Debug: Log the result of the database operation
                logging.info(f"Database update result: {result.raw_result}")
            except Exception as e:
                logging.error(f"Failed to save user to database: {e}")

            await update.message.reply_text(f"Login successful! 🎉\nYour balance is: {balance}")
            await update.message.reply_text(
                "To check your balance, use the /balance command.\n"
                "Use /fetch, /stat, or /bet commands to continue."
                "To log out, use the /logout command."
            )
        else:
            await update.message.reply_text(f"Incorrect phone numuber or password /n")
            await update.message.reply_text(f"Login failed: {login_result['message']}")
        
        # Schedule the password message for deletion
        delete_password_message_later(
            bot=context.bot,  # Pass the bot instance
            chat_id=update.message.chat_id,
            message_id=password_message.message_id,
            delay=40  # Wait for 60 seconds before deleting
        )
        
        # Reset state
        context.user_data['awaiting_password'] = False
    else:
        await update.message.reply_text("Unknown command. Use /start to begin.")

async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /skip command to allow users to proceed without logging in.
    """
    await update.message.reply_text(
        "You have chosen to skip login. Some features may be limited.\n"
        "Use /fetch, /stat, or /bet commands to continue."
    )
    
async def balance_command(update, context):
    """
    Refresh the user's balance using the persistent browser session.
    """
    # Get user details from in-memory data
    user_id = context.user_data.get("user_id")
    phone_number = context.user_data.get("phone_number")

    if not user_id or not phone_number:
        await update.message.reply_text("You are not logged in. Use /login to log in first.")
        return

    # Refresh balance using the session manager in a thread-safe manner
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        validate_sportybet_credentials,
        user_id,
        phone_number,
        None,  # Password is not needed for refresh
        session_manager,
        True  # refresh_only=True
    )

    if result["success"]:
        # Update the balance in the in-memory context
        context.user_data["balance"] = result["balance"]

        # Respond with the updated balance
        await update.message.reply_text(f"Your updated balance is: {result['balance']}")
    else:
        await update.message.reply_text(f"Could not refresh balance: {result['message']}")

async def logout_command(update, context):
    """
    Handle the /logout command. Close the user's browser session.
    """
    user_id = context.user_data.get("user_id")
    if not user_id:
        await update.message.reply_text("You are not logged in.")
        return

    # Use a thread executor to run the synchronous close_session function
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, session_manager.close_session, user_id)
    
    await update.message.reply_text("You have been logged out. Your session has been closed.")
    context.user_data.clear()  # Clear session data
