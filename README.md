# Telegram Group Summary Bot

## Overview
This is a Telegram bot that allows users to log in with their phone numbers, authenticate via Telegram, and retrieve summaries of recent messages from a specified group using an AI-powered language model. The bot utilizes `telethon` for Telegram interactions and `langchain` for AI-generated summaries.

## Features
- User authentication via Telegram phone number and verification code.
- Fetching and summarizing recent messages from a specified group.
- AI-generated summaries using OpenRouterAPI.
- Conversation handling with re-entry support.

## Requirements
Ensure you have the following installed before running the bot:
- Python 3.8+
- Telegram Bot API Token
- API ID and Hash from [my.telegram.org](https://my.telegram.org/)
- OpenRouter API key for AI-generated summaries

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/telegram-group-summary-bot.git
   cd telegram-group-summary-bot
   ```

2. Create a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   Create a `.env` file in the project root and add the following details:
   ```env
   BOT_TOKEN=your_bot_token
   API_ID=your_api_id
   API_HASH=your_api_hash
   OPEN_ROUTER_API=your_openrouter_api_key
   OPEN_ROUTER_BASE=your_openrouter_base_url
   ```

## Usage

1. Start the bot:
   ```sh
   python bot.py
   ```

2. Use the following commands in Telegram:
   - `/start` - Start the bot and get a welcome message.
   - `/login` - Authenticate using your phone number.
   - `/group` - Enter a group name to summarize its recent messages.
   - `/cancel` - Cancel the current operation.

## Workflow
1. User initiates login with `/login`.
2. User provides their phone number.
3. Bot sends an authentication code via Telegram.
4. User enters the code to authenticate.
5. After authentication, the user can enter `/group` and provide a group name. (Bot must be group admin and user must be a participant)
6. The bot fetches recent messages and generates a summary using AI.
7. The user can continue with another group or exit.

## Dependencies
- `python-telegram-bot` for bot interactions.
- `telethon` for Telegram client functionality.
- `langchain` for AI-driven text summarization.
- `dotenv` for environment variable management.
- `python_socks` for proxy support.


## Error Handling
If any step fails (e.g., incorrect code, missing group), the bot will prompt the user to retry or exit.


## Bugs
You have to put a space in code for it to work. If you recieve 12344 code type it as 123 44 in the chatbot.
