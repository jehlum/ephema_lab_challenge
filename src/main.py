import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

load_dotenv()


bot_token = os.getenv("BOT_TOKEN")


async def start(update: Update, context: CallbackContext):
    """Send a greeting when the /start command is issued."""
    await update.message.reply_text("Hello, World!")


def main():
    """Start the bot."""
    app = Application.builder().token(bot_token).build()

    # Command handler for /start
    app.add_handler(CommandHandler("start", start))

    # Run the bot
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
