# Crypto Trading Bot

This bot provides cryptocurrency trading functionalities via Telegram.

## Features

- Calculate AHR999 Index
- Show current market prices
- Place orders (market and limit)
- Scheduled market updates every 30 seconds (for testing, originally every 30 minutes)

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

## 开发日志

### 2023-XX-XX：实现定时市场更新

- 将定时市场更新间隔从30分钟改为30秒，用于测试。
- 问题：预期的每30秒更新没有发送。
- 可能的原因：
  1. 异步任务未正确启动
  2. 主循环阻塞
  3. 更新函数中的错误处理问题
  4. 环境变量问题
  5. 网络问题
  6. API 速率限制
  7. 日志记录问题
  8. 时间同步问题
- 下一步：添加更多日志以诊断问题。

### 2023-XX-XX：调试定时市场更新功能

- 问题：30秒定时推送未生效
- 调试步骤：
  1. 检查 `schedule_market_updates` 函数是否被正确调用
  2. 在 `schedule_market_updates` 和 `send_market_price_update` 函数中添加日志
  3. 确认 `AUTHORIZED_USER_ID` 环境变量设置正确
  4. 检查主循环是否阻塞了其他协程的执行
- 下一步：
  1. 运行更新后的代码，观察日志输出
  2. 如果日志显示函数被调用但消息未发送，检查 Telegram API 连接
  3. 考虑使用 `asyncio.gather` 来并行运行主循环和定时任务
