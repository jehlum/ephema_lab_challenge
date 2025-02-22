import os
from dotenv import load_dotenv
import logging
from datetime import date

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

from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

load_dotenv()

logger = logging.getLogger("my logger")
c_handler = logging.StreamHandler()
logger.addHandler(c_handler)
logger.setLevel(logging.INFO)

bot_token = os.getenv("BOT_TOKEN")
web_api_id = os.getenv("API_ID")
web_api_hash = os.getenv("API_HASH")
open_router_api = os.getenv("OPEN_ROUTER_API")
open_router_base = os.getenv("OPEN_ROUTER_BASE")

llm = ChatOpenAI(
    openai_api_key=open_router_api,
    openai_api_base=open_router_base,
    model_name="cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
)

# Store user sessions
user_sessions = {}

# Conversation states
ENTER_PHONE, ENTER_CODE, FIND_GROUP, CONTINUE, CANCEL = range(5)


async def start(update: Update, context: CallbackContext):
    """Send a welcome message and guide users to login."""

    await update.message.reply_text("Welcome! Use /login to authenticate.")


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

        return CANCEL


async def get_code(update: Update, context: CallbackContext):
    """Verify the entered code."""
    user_id = update.message.chat_id
    code = update.message.text

    if user_id not in user_sessions:
        await update.message.reply_text("Session expired. Please use /login again.")
        return CANCEL

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

        return CANCEL


async def group(update: Update, context: CallbackContext):
    """Initiate the login process."""
    await update.message.reply_text("Please enter your group handle :).")
    logger.info("finding group")

    return FIND_GROUP


async def find_group(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    group_name = update.message.text
    client = user_sessions[user_id]["client"]

    try:

        dialogs = await client.get_dialogs()

        me = await client.get_me()

        people = await client.get_participants(group_name)

    except Exception as e:
        await update.message.reply_text(
            f"Group not found :( Error message: {e} \n Type Yes if you want have another name! Type No to quit"
        )

        return CONTINUE

    complete_chat = ""

    for user in people:

        if user.id == me.id:

            async for message in client.iter_messages(
                group_name, limit=10, reverse=False
            ):
                print(message.id, message.text)
                complete_chat += f" message id {message.id} " + message.text

    if complete_chat:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Write a concise summary of the following Do not enter message id summerize what is going on and what is being discussed :\\n\\n{context}",
                )
            ]
        )
        print(complete_chat)

        llm_chain = LLMChain(prompt=prompt, llm=llm)
        result = llm_chain.invoke({"context": complete_chat})
        await update.message.reply_text(result.text)
        await update.message.reply_text(
            """Type "Yes" to enter another group name. Type "No" to quit"""
        )
        return CONTINUE

    await update.message.reply_text(
        f"""You are not a part of the group. Type "Yes" to enter another group name. Type "No" to quit."""
    )
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


async def cancel(update: Update, context: CallbackContext):
    """Handle user cancellation."""
    await update.message.reply_text("Process canceled.")
    user_id = update.message.chat_id

    if user_id not in user_sessions:
        return ConversationHandler.END
    client = user_sessions[user_id]["client"]
    client.disconnect()

    user_sessions.pop(user_id, None)
    return ConversationHandler.END


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
            CANCEL: [cancel],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(group_conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv_handler)

    logger.info("Started")

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
