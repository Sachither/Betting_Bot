# app/bot/listener.py
"""
This module handles the bot's webhook listener and registers handlers from commands.py.
It keeps listener.py lightweight and focused only on managing the bot's lifecycle.
"""

import logging
import os
import pytz
from telegram import Update
from telegram.ext import Application, JobQueue, CommandHandler, MessageHandler, filters
from app.bot.commands import (
    login_command,
    skip_command,
    start_command,
    help_command,
    balance_command,
    text_handler,
    logout_command
)  # Import handlers from commands.py
from fastapi import Request, Response

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce httpx logs

logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Global application object
application: Application = None


async def webhook_handler(request: Request):
    """
    FastAPI webhook handler to receive updates from Telegram.
    """
    request_json = await request.json()
    try:
        update = Update.de_json(request_json, application.bot)
        if application:
            await application.process_update(update)
            return Response(status_code=200)
        else:
            logger.error("Application not initialized in webhook_handler.")
            return Response(status_code=500, content="Application not initialized")
    except Exception as e:
        logger.error(f"Webhook handler error: {e}", exc_info=True)
        return Response(status_code=500, content="Webhook handler error")


async def start_bot_listener(webhook_url: str) -> None:
    """
    Start the Telegram bot listener using webhooks.
    """
    global application
    logger.info("Starting Telegram bot listener...")

    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token not provided. Bot listener cannot start.")
        return
    if not webhook_url:
        logger.error("Webhook URL not provided. Bot listener cannot start.")
        return

    if application is None:
        logger.info("Building Telegram bot application...")
        try:
            job_queue = JobQueue()
            job_queue.scheduler.timezone = pytz.utc
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).job_queue(job_queue).build()
            await application.initialize()
            logger.info("Telegram bot application built and initialized.")
        except Exception as app_build_exception:
            logger.error(f"Error building Telegram bot application: {app_build_exception}", exc_info=True)
            return
    else:
        logger.info("Telegram bot application already initialized.")

    try:
        # Register commands handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("login", login_command))  
        application.add_handler(CommandHandler("skip", skip_command)) 
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("logout", logout_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
        logger.info("Command handlers registered.")
    except Exception as handler_error:
        logger.error(f"Error registering command handlers: {handler_error}", exc_info=True)
        return

    webhook_full_url = f"{webhook_url}/webhook"
    logger.info(f"Attempting to set webhook: {webhook_full_url}")
    try:
        webhook_status = await application.bot.set_webhook(webhook_full_url)
        logger.info(f"Webhook set up status: {webhook_status}")
        logger.info(f"Webhook URL set to: {webhook_full_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}", exc_info=True)
        return

    # Add FastAPI route for webhook
    from main import app
    app.add_api_route("/webhook", webhook_handler, methods=["POST"])
    logger.info("FastAPI webhook route added.")

    logger.info("Telegram bot listener started with webhook.")
