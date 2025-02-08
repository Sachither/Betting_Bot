import logging
import os
import pytz
from telegram.ext import Application, CommandHandler, MessageHandler, filters, JobQueue
from fastapi import FastAPI, Request, Response
from telegram import Update

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # Reduce httpx logs

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

application: Application = None

async def start_command_handler(update: Update, context):
    """Handles the /start command."""
    await update.message.reply_text("Hello! I am your betting bot. Use /help to see commands.")

async def help_command_handler(update: Update, context):
    """Handles the /help command."""
    help_text = """
    I am a betting bot. Here are the commands you can use:

    /start - Start the bot and get a welcome message.
    /help - Display this help text.
    (any text) - I will echo back any text you send me.
    """
    await update.message.reply_text(help_text)

async def echo(update: Update, context):
    """Echoes back the user message."""
    if update.message and update.message.text:
        user_message = update.message.text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=user_message)

async def webhook_handler(request: Request):
    """FastAPI webhook handler to receive updates from Telegram."""
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
    """Start the Telegram bot listener using webhooks."""
    global application
    logger.info("Starting Telegram bot listener...") # Keep start log

    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token not provided. Bot listener cannot start.")
        return
    if not webhook_url:
        logger.error("Webhook URL not provided. Bot listener cannot start.")
        return

    if application is None:
        logger.info("Building Telegram bot application...") # Keep application build log
        try:
            job_queue = JobQueue()
            job_queue.scheduler.timezone = pytz.utc
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).job_queue(job_queue).build()
            await application.initialize()
            logger.info("Telegram bot application built and initialized.") # Keep app init log
        except Exception as app_build_exception:
            logger.error(f"Error building Telegram bot application: {app_build_exception}", exc_info=True)
            return
    else:
        logger.info("Telegram bot application already initialized.")

    try:
        application.add_handler(CommandHandler("start", start_command_handler))
        application.add_handler(CommandHandler("help", help_command_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        logger.info("Command handlers registered.") # Keep handler registration log
    except Exception as handler_error:
        logger.error(f"Error registering command handlers: {handler_error}", exc_info=True)
        return

    webhook_full_url = f"{webhook_url}/webhook"
    logger.info(f"Attempting to set webhook: {webhook_full_url}") # Keep webhook attempt log
    try:
        webhook_status = await application.bot.set_webhook(webhook_full_url)
        logger.info(f"Webhook set up status: {webhook_status}")
        logger.info(f"Webhook URL set to: {webhook_full_url}") # Keep webhook URL log
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}", exc_info=True)
        return

    from main import app
    app.add_api_route("/webhook", webhook_handler, methods=["POST"])
    logger.info("FastAPI webhook route added.") # Keep FastAPI route log

    logger.info("Telegram bot listener started with webhook.") # Keep final start log