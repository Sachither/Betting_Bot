import threading
import asyncio
import logging

def delete_password_message_later(bot, chat_id, message_id, delay=40):
    """
    Delete the password message after a delay using threading.

    Args:
        bot: Telegram Bot instance.
        chat_id: ID of the chat where the message was sent.
        message_id: ID of the message to be deleted.
        delay: Time to wait before deleting the message (in seconds).
    """
    def delete_message(loop):
        try:
            # Wait for the specified delay
            threading.Event().wait(delay)

            # Run the coroutine thread-safely in the provided event loop
            coroutine = bot.delete_message(chat_id=chat_id, message_id=message_id)
            asyncio.run_coroutine_threadsafe(coroutine, loop).result()  # Wait for the coroutine to complete
        except Exception as e:
            logging.error(f"Failed to delete password message: {e}")

    # Get the current event loop (from the main thread)
    loop = asyncio.get_event_loop()

    # Start the deletion process in a new thread
    threading.Thread(target=delete_message, args=(loop,)).start()
