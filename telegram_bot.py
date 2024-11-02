import logging
import os
import asyncio
from time import sleep
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.error import NetworkError

from models.price_prediction import calculate_ahr999, get_current_price
from models.investment_advice import get_investment_advice
from binance_api.market_data import get_top_crypto_data, format_crypto_data
from binance_api import trading_api, init_trading_api

# 设置你的bot token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHORIZED_USER_ID = int(os.getenv('AUTHORIZED_USER_ID'))

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

class Context:
    def __init__(self):
        self.user_data = {}

context = Context()

TOP_CRYPTOS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 
                'DOGEUSDT', 'SOLUSDT', 'TRXUSDT', 'DOTUSDT', 'SHIBUSDT',
                'SUIUSDT', 'POLUSDT']
AMOUNT_OPTIONS = [5, 50, 100, 500, 1000]  # USDT 金额选项

# 从环境变量中获取验证码
CONFIRMATION_CODE = os.getenv('CONFIRMATION_CODE')
ORDER_TYPES = ['Market', 'Limit']

def is_authorized(user_id):
    return user_id == AUTHORIZED_USER_ID

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Calculate AHR999 Index", callback_data='calculate_ahr999')],
        [InlineKeyboardButton("Current Market Price", callback_data='market_price')],
        [InlineKeyboardButton("Place Order", callback_data='place_order')],
        [InlineKeyboardButton("Order Status", callback_data='order_status')],
        [InlineKeyboardButton("Order History", callback_data='order_history')],  # 增
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(bot, update):
    logger.info(f"User {update.effective_user.id} started the bot")
    await bot.send_message(
        chat_id=update.effective_chat.id,
        text='Welcome to the Crypto Trading Bot!\n\n'
             'Please select an option from the menu below:',
        reply_markup=get_main_menu_keyboard()
    )

async def button_callback(bot, update):
    try:
        query = update.callback_query
        logger.info("="*50)
        logger.info(f"[button_callback] Starting with data: {query.data}")
        logger.info(f"[button_callback] User ID: {query.from_user.id}")
        logger.info(f"[button_callback] Current context: {context.user_data}")
        
        if query.data == 'place_order':
            logger.info("[button_callback] Detected place_order command")
            await show_order_menu(bot, query)
    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        logger.error("Full error details:", exc_info=True)

async def calculate_ahr999_index(bot, query):
    try:
        ahr999_value, timestamp = await calculate_ahr999()
        current_price = await get_current_price()
        
        investment_advice = get_investment_advice(ahr999_value)
        
        ahr999_message = (
            f"Current BTC Price: ${format_number(current_price)}\n"
            f"AHR999 Index: {format_number(ahr999_value, 4)}\n"
            f"Calculation Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Investment Advice: {investment_advice}"
        )
        
        await bot.send_message(
            chat_id=query.message.chat_id,
            text=ahr999_message,
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error calculating AHR999: {str(e)}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="Sorry, an error occurred while calculating the AHR999 index or getting BTC price. Please try again later.",
            reply_markup=get_main_menu_keyboard()
        )

async def show_market_price(bot, query):
    try:
        crypto_data = await get_top_crypto_data()
        formatted_data = await format_crypto_data(crypto_data)
        
        message = "Top 10 Cryptocurrencies Market Data:\n\n"
        for data in formatted_data:
            message += f"{data['symbol']}:\n"
            message += f"Price: ${format_number(data['price'])}\n"
            message += f"24h Change: {format_number(data['change'], 2)}%\n"
            message += f"24h High: ${format_number(data['high'])}\n"
            message += f"24h Low: ${format_number(data['low'])}\n"
            message += f"24h Volume: {format_number(data['volume'])} USDT\n\n"

        if len(message) > 4096:
            messages = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for msg in messages:
                await bot.send_message(
                    chat_id=query.message.chat_id,
                    text=msg
                )
        else:
            await bot.send_message(
                chat_id=query.message.chat_id,
                text=message
            )
        
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="What would you like to do next?",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"获取市场价格时发生错误: {str(e)}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="抱歉，获取市场价格时出现错误。请稍后再试。",
            reply_markup=get_main_menu_keyboard()
        )

async def show_order_menu(bot, query):
    user_id = query.from_user.id
    logger.info("="*50)
    logger.info(f"[show_order_menu] Starting for user {user_id}")
    logger.info(f"[show_order_menu] Context data before: {context.user_data}")
    logger.info(f"[show_order_menu] User state before: {context.user_data.get(user_id, {}).get('state')}")
    
    if user_id not in context.user_data:
        logger.info(f"[show_order_menu] Creating new user data for {user_id}")
        context.user_data[user_id] = {}
    context.user_data[user_id]['state'] = 'waiting_for_confirmation_code'
    
    logger.info(f"[show_order_menu] Context data after: {context.user_data}")
    logger.info(f"[show_order_menu] User state after: {context.user_data[user_id]['state']}")
    
    if not is_authorized(query.from_user.id):
        await bot.answer_callback_query(query.id, text="You are not authorized to place orders.")
        return

    await bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Please enter the 6-digit confirmation code to proceed placing order:"
    )

async def handle_confirmation_code(bot, message):
    user_id = message.from_user.id
    logger.info("="*50)
    logger.info(f"[handle_confirmation_code] Starting for user {user_id}")
    logger.info(f"[handle_confirmation_code] Input code: {message.text}")
    logger.info(f"[handle_confirmation_code] Context data: {context.user_data}")
    logger.info(f"[handle_confirmation_code] User state: {context.user_data.get(user_id, {}).get('state')}")
    logger.info(f"Input code: {message.text}, Expected code: {CONFIRMATION_CODE}")
    logger.info(f"User state before handling: {context.user_data.get(user_id, {}).get('state')}")
    logger.info(f"Full context data: {context.user_data}")
    
    # 检查用户状态是否正确
    current_state = context.user_data.get(user_id, {}).get('state')
    if current_state != 'waiting_for_confirmation_code':
        logger.info(f"Unexpected state: {current_state}, expected: waiting_for_confirmation_code")
        return
    
    if message.text == CONFIRMATION_CODE:
        keyboard = [
            [InlineKeyboardButton(f"{order_type} Order", callback_data=f'order_type_{order_type}') for order_type in ORDER_TYPES]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=message.chat_id,
            text="Confirmation code correct. Please select order type:",
            reply_markup=reply_markup
        )
        context.user_data[user_id]['state'] = 'selecting_order_type'
        logger.info(f"State updated to: {context.user_data[user_id]['state']}")
    else:
        await bot.send_message(
            chat_id=message.chat_id,
            text="Invalid confirmation code. Order process cancelled.",
            reply_markup=get_main_menu_keyboard()
        )
        # 只清除状态，不清除整个用户数据
        context.user_data[user_id]['state'] = None

async def handle_order_type_selection(bot, query):
    order_type = query.data.split('_')[2]
    context.user_data['order_type'] = order_type
    
    # 创建一个包含所有选项的键盘
    keyboard = []
    for crypto in TOP_CRYPTOS:
        row = [
            InlineKeyboardButton(f"{crypto} BUY", callback_data=f'order_{crypto}_BUY'),
            InlineKeyboardButton(f"{crypto} SELL", callback_data=f'order_{crypto}_SELL')
        ]
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=f"Selected order type: {order_type}\nPlease select a trading pair and side:",
        reply_markup=reply_markup
    )

async def handle_order_selection(bot, query):
    try:
        parts = query.data.split('_')
        logger.info(f"Order selection parts: {parts}")  # 添加日志
        
        if len(parts) >= 3:
            _, symbol, side = parts
            context.user_data['symbol'] = symbol
            context.user_data['side'] = side
            
            # 创建一个包含金额选项的键盘
            keyboard = [[InlineKeyboardButton(f"{amount} USDT", callback_data=f'amount_{amount}')] for amount in AMOUNT_OPTIONS]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"Selected: {symbol} {side}\nPlease select the amount:",
                reply_markup=reply_markup
            )
        else:
            logger.error(f"Invalid order selection format: {query.data}")
            await bot.send_message(
                chat_id=query.message.chat_id,
                text="Invalid order selection. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in handle_order_selection: {str(e)}")
        logger.error(f"Query data: {query.data}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="An error occurred while processing your selection. Please try again.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_amount_selection(bot, query):
    amount = float(query.data.split('_')[1])
    context.user_data['amount'] = amount
    
    if context.user_data['order_type'] == 'Limit':
        await bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Please enter the limit price:"
        )
        context.user_data['state'] = 'waiting_for_limit_price'
    else:
        await show_order_confirmation(bot, query)

async def handle_limit_price_input(bot, message):
    try:
        price = float(message.text)
        context.user_data['price'] = price
        await show_order_confirmation(bot, message)
    except ValueError:
        await bot.send_message(
            chat_id=message.chat_id,
            text="Invalid price. Please enter a valid number."
        )

async def show_order_confirmation(bot, update):
    symbol = context.user_data['symbol']
    side = context.user_data['side']
    amount = context.user_data['amount']
    order_type = context.user_data['order_type']
    
    confirmation_text = (
        f"Order Summary:\n"
        f"Type: {order_type}\n"
        f"Symbol: {symbol}\n"
        f"Side: {side}\n"
        f"Amount: {amount} USDT\n"
    )
    
    if order_type == 'Limit':
        price = context.user_data['price']
        confirmation_text += f"Price: {price}\n"
    
    confirmation_text += "\nDo you confirm this order?"
    
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_order')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if isinstance(update, CallbackQuery):
        await bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id,
            text=confirmation_text,
            reply_markup=reply_markup
        )
    else:
        await bot.send_message(
            chat_id=update.chat_id,
            text=confirmation_text,
            reply_markup=reply_markup
        )

async def handle_order_confirmation(bot, query):
    if query.data == 'confirm_order':
        try:
            symbol = context.user_data['symbol']
            side = context.user_data['side']
            amount = context.user_data['amount']
            order_type = context.user_data['order_type']
            
            logger.info(f"Attempting to place order: symbol={symbol}, side={side}, amount={amount}, type={order_type}")
            
            if order_type == 'Market':
                logger.info("Placing market order")
                order = await trading_api.place_market_order(symbol, side, amount)
            else:  # Limit
                price = context.user_data['price']
                logger.info(f"Placing limit order with price: {price}")
                order = await trading_api.place_limit_order(symbol, side, amount, price)
            
            if order:
                logger.info(f"Order placed successfully: {order}")
                await bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text=f"Order placed successfully!\nOrder ID: {order['orderId']}",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                logger.error("Order placement failed: No order returned from API")
                await bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text="Failed to place the order. Please check logs for details.",
                    reply_markup=get_main_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in handle_order_confirmation: {str(e)}")
            await bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"An error occurred while placing the order: {str(e)}",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        logger.info("Order cancelled by user")
        await bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Order cancelled.",
            reply_markup=get_main_menu_keyboard()
        )
    
    context.user_data.clear()

async def show_order_status(bot, query):
    try:
        # 使用 trading_api 实例调用 get_open_orders 方法
        orders = await trading_api.get_open_orders()
        
        if not orders:
            await bot.send_message(
                chat_id=query.message.chat_id,
                text="You have no open orders.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        message = "Your open orders:\n\n"
        for order in orders:
            message += f"Symbol: {order['symbol']}\n"
            message += f"Order ID: {order['orderId']}\n"
            message += f"Type: {order['type']}\n"
            message += f"Side: {order['side']}\n"
            message += f"Price: {order['price']}\n"
            message += f"Amount: {order['origQty']}\n"
            message += f"Status: {order['status']}\n\n"

        await bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in show_order_status: {str(e)}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="An error occurred while fetching order status. Please try again later.",
            reply_markup=get_main_menu_keyboard()
        )

async def show_help(bot, query):
    help_text = (
        "Welcome to the Crypto Trading Bot!\n\n"
        "Here are the available commands:\n"
        "- Calculate AHR999 Index: Get the current AHR999 index and investment advice\n"
        "- Current Market Price: Check current prices for top 10 cryptocurrencies\n"
        "- Place Order: Place a new order (requires confirmation code)\n"
        "- Order Status: (Coming soon) Check your order status\n"
        "- Order History: (Coming soon) Check your order history\n"
        "- Help: Show this help message"
    )
    await bot.send_message(
        chat_id=query.message.chat_id,
        text=help_text,
        reply_markup=get_main_menu_keyboard()
    )

async def handle_message(bot, update):
    logger.info(f"Received message from user {update.effective_user.id}: {update.message.text}")
    await start(bot, update)

async def process_update(bot, update):
    try:
        user_id = update.effective_user.id
        logger.info("="*50)
        logger.info(f"[process_update] Starting for user {user_id}")
        logger.info(f"[process_update] Update type: {type(update)}")
        logger.info(f"[process_update] Full update: {update.to_dict()}")
        logger.info(f"[process_update] Context data: {context.user_data}")
        
        # 处理回调查询（按钮点击）
        if update.callback_query:
            query = update.callback_query
            logger.info(f"[process_update] Received callback query with data: {query.data}")
            
            # 处理各种回调
            if query.data == 'place_order':
                logger.info("[process_update] Handling place_order")
                await show_order_menu(bot, query)
                return
            elif query.data == 'order_history':
                logger.info("[process_update] Handling order_history")
                await show_order_history(bot, query)
                return
            elif query.data == 'calculate_ahr999':
                logger.info("[process_update] Handling calculate_ahr999")
                await calculate_ahr999_index(bot, query)
                return
            elif query.data == 'market_price':
                logger.info("[process_update] Handling market_price")
                await show_market_price(bot, query)
                return
            elif query.data == 'order_status':
                logger.info("[process_update] Handling order_status")
                await show_order_status(bot, query)
                return
            elif query.data == 'help':
                logger.info("[process_update] Handling help")
                await show_help(bot, query)
                return
            
            # 处理复杂回调
            if '_' in query.data:
                logger.info(f"[process_update] Processing complex callback: {query.data}")
                parts = query.data.split('_')
                logger.info(f"[process_update] Split callback data parts: {parts}")
                
                if query.data.startswith('order_type_'):
                    await handle_order_type_selection(bot, query)
                elif query.data.startswith('amount_'):
                    await handle_amount_selection(bot, query)
                elif len(parts) == 3 and parts[0] == 'order':
                    await handle_order_selection(bot, query)
                elif query.data in ['confirm_order', 'cancel_order']:
                    await handle_order_confirmation(bot, query)
                else:
                    logger.warning(f"[process_update] Unhandled complex callback: {query.data}")
        
        # 处理消息
        if update.message:
            logger.info(f"[process_update] Message text: {update.message.text}")
            current_state = context.user_data.get(user_id, {}).get('state')
            logger.info(f"[process_update] Current state: {current_state}")
            
            if current_state == 'waiting_for_confirmation_code':
                logger.info("[process_update] Handling confirmation code")
                await handle_confirmation_code(bot, update.message)
                return
            elif current_state == 'waiting_for_limit_price':
                logger.info("[process_update] Handling limit price input")
                await handle_limit_price_input(bot, update.message)
                return
            else:
                logger.info(f"[process_update] No specific state, showing main menu")
                await start(bot, update)
                
    except Exception as e:
        logger.error("="*50)
        logger.error(f"Error in process_update: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error("Full error details:", exc_info=True)
        logger.error("="*50)

async def send_market_price_update(bot):
    try:
        crypto_data = await get_top_crypto_data()
        formatted_data = await format_crypto_data(crypto_data)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Scheduled Market Update (as of {current_time}):\n\n"
        
        for data in formatted_data:
            message += f"{data['symbol']}:\n"
            message += f"Price: ${format_number(data['price'])}\n"
            message += f"24h Change: {format_number(data['change'], 2)}%\n\n"

        # 这里应该从数据库或某个存储中获取订阅用户的列
        # 暂时我们只发送给授用户
        await bot.send_message(
            chat_id=AUTHORIZED_USER_ID,
            text=message
        )
    except Exception as e:
        logger.error(f"Error in scheduled market price update: {str(e)}")
        logger.error(f"Formatted data: {formatted_data}")  # 添加这行来记录格化后的数据

async def schedule_market_updates(bot):
    while True:
        try:
            await send_market_price_update(bot)
        except Exception as e:
            logger.error(f"Error in schedule_market_updates: {str(e)}")
        await asyncio.sleep(3600)  # 等待3600秒（1小时）

async def main():
    await init_trading_api()
    bot = Bot(TOKEN)
    logger.info("Starting bot")
    
    # 创建并运行两个任务
    update_task = asyncio.create_task(run_main_loop(bot))
    market_update_task = asyncio.create_task(schedule_market_updates(bot))
    
    try:
        # 等待两个任务完成（实际上它们会一直运行）
        await asyncio.gather(update_task, market_update_task)
    except asyncio.CancelledError:
        logger.info("Tasks were cancelled")
    finally:
        # 确保任务被正确清理
        update_task.cancel()
        market_update_task.cancel()
        await asyncio.gather(update_task, market_update_task, return_exceptions=True)

async def run_main_loop(bot):
    offset = 0
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                offset = update.update_id + 1
                await process_update(bot, update)
        except NetworkError:
            sleep(1)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            sleep(1)

async def show_order_history(bot, query):
    try:
        print("Starting to fetch order history...")  # 新增
        orders = await trading_api.get_order_history()
        print(f"Received orders: {orders}")  # 新增
        
        if not orders:
            print("No orders found")  # 新增
            await bot.send_message(
                chat_id=query.message.chat_id,
                text="You have no order history in the last 24 hours.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        message = "Your order history (last 24 hours):\n\n"
        for index, order in enumerate(orders, start=1):
            try:
                print(f"Processing order {index}: {order}")  # 新增
                message += f"{index}. Time: {datetime.fromtimestamp(order.get('time', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += f"   Symbol: {order.get('symbol', 'N/A')}\n"
                message += f"   Type: {order.get('type', 'N/A')}\n"
                message += f"   Side: {order.get('side', 'N/A')}\n"
                message += f"   Price: {order.get('price', 'N/A')}\n"
                message += f"   Amount: {order.get('origQty', 'N/A')}\n"
                message += f"   Status: {order.get('status', 'N/A')}\n\n"
            except Exception as e:
                print(f"Error processing order {index}: {e}")  # 新增
                print(f"Order data: {order}")  # 新增
                logger.error(f"Error processing order {index}: {str(e)}")
                logger.error(f"Order data: {order}")
                message += f"{index}. Error processing this order\n\n"

        # 如果消息太长，分割发送
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await bot.send_message(
                    chat_id=query.message.chat_id,
                    text=message[i:i+4096]
                )
        else:
            await bot.send_message(
                chat_id=query.message.chat_id,
                text=message
            )
        
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="What would you like to do next?",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in show_order_history: {str(e)}")
        logger.error(f"Orders data: {orders}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="An error occurred while fetching order history. Please try again later.",
            reply_markup=get_main_menu_keyboard()
        )

def run_bot():
    logger.info("Starting bot from run_bot function")
    asyncio.run(main())

def format_number(number, decimal_places=2):
    return f"{number:,.{decimal_places}f}"

if __name__ == '__main__':
    run_bot()
