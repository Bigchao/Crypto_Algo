# Crypto Trading Bot

This bot provides cryptocurrency trading functionalities via Telegram.

## Features

- Calculate AHR999 Index
- Show current market prices
- Place orders (market and limit)
- Scheduled market updates every 30 minutes

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crypto-trading-bot.git
   cd crypto-trading-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables in a `.env` file:
   ```bash
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   AUTHORIZED_USER_ID=your_telegram_user_id
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## Usage

Start the bot in Telegram and use the provided menu to access different functionalities.
