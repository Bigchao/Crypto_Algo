# Crypto Trading Bot

这是一个基于 Telegram 的加密货币交易机器人，提供多种功能来帮助用户进行加密货币交易和市场分析。

## 主要功能

- 计算 AHR999 指数并提供投资建议
- 显示当前市场价格（包括 12 种主要加密货币）
- 下单功能（市价单和限价单）
- 查看订单状态和订单历史
- 每小时自动推送市场更新

## 当前存在的问题

### 1. Order History 功能
- 问题描述：点击 Order History 按钮后无法正确显示订单历史
- 可能原因：
  - Binance API 的地理位置限制
  - API 调用参数不正确
  - 需要处理多个交易对的订单历史
- 状态：正在通过添加详细日志进行调试

### 2. 下单金额选择问题
- 问题描述：在选择下单金额时出现错误（'amount' KeyError）
- 可能原因：
  - 用户数据状态管理问题
  - 回调数据处理不正确
  - 上下文数据存储结构问题
- 状态：正在通过添加详细日志追踪数据流

### 3. 资源管理问题
- 问题描述：程序退出时出现 "Unclosed client session" 警告
- 可能原因：aiohttp 客户端会话未正确关闭
- 状态：需要改进资源清理机制

## 最新开发进展

1. 添加了详细的日志记录：
   - 在 handle_amount_selection 中添加了完整的数据流追踪
   - 在状态转换的关键点添加了日志
   - 改进了错误处理和异常信息记录

2. 正在进行的工作：
   - 调试 Order History 功能的 API 调用
   - 优化用户数据状态管理
   - 改进错误处理机制

## 环境设置

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/crypto-trading-bot.git
   cd crypto-trading-bot
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 在 `.env` 文件中设置环境变量：
   ```
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   AUTHORIZED_USER_ID=your_telegram_user_id
   ```

4. 运行机器人：
   ```bash
   python main.py
   ```

## 使用说明

1. 在 Telegram 中启动机器人。
2. 使用提供的菜单访问不同的功能：
   - 计算 AHR999 指数
   - 查看当前市场价格
   - 下单（需要确认码）
   - 查看订单状态和订单历史（部分功能待修复）
   - 帮助

## 项目结构

- `main.py`: 程序入口点
- `telegram_bot.py`: Telegram 机器人的主要逻辑
- `binance_api/`: 与 Binance API 交互的模块
- `models/`: 包含价格预测和投资建议的模型
- `data/`: 存储历史数据和模型参数

## 开发日志

### 最新更新：问题修复中

- Order History 功能问题排查中
- 下单金额选择功能问题排查中
- 添加了更详细的日志记录
- 改进了错误处理机制

### 之前的更新

- 实现了 AHR999 指数计算功能
- 添加了市场价格查询功能
- 实现了下单功能（包括市价单和限价单）
- 优化了错误处理和日志记录

## 未来计划

- 修复当前存在的问题
- 优化性能和稳定性
- 添加更多交易策略
- 改进用户界面和交互体验
- 增强安全性和错误处理机制
- 完善测试和文档

## 贡献

欢迎提交 pull requests 来改进这个项目。对于重大更改，请先开一个 issue 讨论您想要改变的内容。

## 许可

本项目采用 [MIT 许可证](https://choosealicense.com/licenses/mit/)。
