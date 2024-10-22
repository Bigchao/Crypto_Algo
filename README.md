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

### 2023-XX-XX：重构定时任务实现

- 问题：使用 `aioschedule` 导致与 `asyncio` 的兼容性问题
- 解决方案：
  1. 移除 `aioschedule` 相关代码
  2. 使用 `asyncio` 原生功能重新实现定时任务
  3. 在 `main()` 函数中使用 `asyncio.create_task()` 创建并行任务
- 修改内容：
  1. 重写 `schedule_market_updates` 函数，使用 `asyncio.sleep()` 实现定时功能
  2. 更新 `main()` 函数，使用 `asyncio.create_task()` 和 `asyncio.gather()` 并行运行任务
  3. 添加错误处理和任务取消逻辑，确保程序可以优雅关闭
- 预期结果：定时更新和主循环能够并行运行，不会相互阻塞
- 下一步：运行更新后的代码，观察定时推送是否正常工作，并监控错误日志

### 2023-XX-XX：成功实现异步推送

- 成功实现：
  - 移除了 `aioschedule` 依赖
  - 使用 `asyncio` 原生功能重新实现了定时任务
  - 成功实现了异步推送，每30秒发送一次市场更新

- 下一步可能的改进方向：
  1. 性能优化：
     - 监控 CPU 和内存使用情况
     - 考虑使用缓存机制减少 API 请求频率
  2. 功能扩展：
     - 实现用户订阅/取消订阅市场更新功能
     - 添加更多交易对或自定义交易对选择
  3. 错误处理和日志：
     - 增强错误处理机制，添加更详细的日志记录
     - 实现错误通知机制
  4. 用户体验改进：
     - 优化消息格式，使市场更新更易读
     - 添加图表或可视化元素
  5. 安全性：
     - 实现更强大的用户认证机制
     - 添加交易限额和风险控制措施
  6. 测试：
     - 编写单元测试和集成测试
     - 进行长时间的稳定性测试
  7. 文档更新：
     - 更新 README.md
     - 创建详细的开发文档
  8. 代码清理：
     - 检查并移除不再使用的代码或导入
     - 确保代码风格一致，符合 PEP 8 标准

## 未来计划

- 优化性能和稳定性
- 扩展功能集
- 改进用户界面和体验
- 增强安全性和错误处理
- 完善测试和文档
