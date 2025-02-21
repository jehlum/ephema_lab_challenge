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
from python_socks import ProxyType

load_dotenv()

logger = logging.getLogger("my logger")
c_handler = logging.StreamHandler()
logger.addHandler(c_handler)
logger.setLevel(logging.INFO)

bot_token = os.getenv("BOT_TOKEN")
web_api_id = os.getenv("API_ID")
web_api_hash = os.getenv("API_HASH")

# Store user sessions
user_sessions = {}

# Conversation states
ENTER_PHONE, ENTER_CODE, FIND_GROUP, CONTINUE = range(4)


async def start(update: Update, context: CallbackContext):
    """Send a welcome message and guide users to login."""

    await update.message.reply_text("Welcome! Use /login to authenticate.")


async def group(update: Update, context: CallbackContext):
    """Initiate the login process."""
    await update.message.reply_text("Please enter your group handle :).")
    logger.info("finding group")

    return FIND_GROUP


async def find_group(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    group_name = update.message.text
    client = user_sessions[user_id]["client"]

    group_name = "@" + group_name
    try:
        group = await client.get_entity(group_name)
    except Exception as e:
        await update.message.reply_text(
            f"Group not found :( Error message: {e} \n Type Yes if you want have another name! Type No to quit"
        )

        return CONTINUE

    people = await client.get_participants(group)
    if user_id not in people:
        await update.message.reply_text(f"You are not a part of the group. Sorry!")
        return CONTINUE

    # get last 10 messages
    return CONTINUE


async def continue_handler(update: Update, context: CallbackContext) -> int:
    """Handle user's decision to continue or stop."""
    response = update.message.text.strip().lower()

    if response in ["yes", "y"]:
        await update.message.reply_text("Please enter another group name:")
        return FIND_GROUP
    elif response in ["no", "n"]:
        await update.message.reply_text(
            "Thank you for using the service. Use /group if you need to access messages again."
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please answer with 'yes' or 'no'.")
        return CONTINUE


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
    session_name = f"user_{user_id}"
    # host":"","port":,"secret":"","country":"US","up":561,"down":0,"uptime":100,"addTime":1739271887,"updateTime":1739876912,"ping":92
    logger.info(f"Starting session  :  {session_name}")
    # "host":"","port":,"secret":"","country":"US","up":105,"down":0,"uptime":100,"addTime":1733980213,"updateTime":1740029073,"ping":173},
    # proxy = (
    #     "137.184.11.122",
    #     443,
    #     "eec4d42116432e4e1bb8d184f9f8dc1b627777772e6d6963726f736f66742e636f6d",
    # )

    # my_proxy = {
    #     "proxy_type": ProxyType.HTTP,  # (mandatory) protocol to use (see above)
    #     "addr": "137.184.11.122",  # (mandatory) proxy IP address
    #     "port": 443,  # (mandatory) proxy port number
    # }

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
        await update.message.reply_text(
            f"Login successful! Welcome, {me.first_name}.Use /group command to summerize messages from that group :)"
        )

        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Login failed: {e}")
        client.disconnect()
        return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    """Handle user cancellation."""
    await update.message.reply_text("Process canceled.")
    user_id = update.message.chat_id

    return ConversationHandler.END


async def find_group(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    if user_id not in user_sessions:
        await update.message.reply_text("Session expired. Please use /login again.")
        return ConversationHandler.END

    client = user_sessions[user_id]["client"]

    temp_group = "@TopTechProgramsChannel"
    group = await client.get_entity(temp_group)
    people = await client.get_participants(group)
    if user_id in people:
        print("HI")


def main():
    """Start the bot."""

    app = Application.builder().token(bot_token).build()

    login_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)
            ],
            ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
            # LOOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_group)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    group_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("group", group)],
        states={
            FIND_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_group)],
            CONTINUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, continue_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(group_conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv_handler)

    logger.info("Started")

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
