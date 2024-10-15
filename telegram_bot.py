import logging
import os
import asyncio
from time import sleep
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError

from models.price_prediction import calculate_ahr999, get_current_price
from models.investment_advice import get_investment_advice
from binance_api.market_data import get_top_crypto_data, format_crypto_data
from binance_api.trading import trading_api, init_trading_api

# 设置你的bot token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHORIZED_USER_ID = int(os.getenv('AUTHORIZED_USER_ID'))

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# 在文件开头添加这个类定义
class Context:
    def __init__(self):
        self.user_data = {}

# 全局 context 对象
context = Context()

TOP_CRYPTOS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 
                'DOGEUSDT', 'SOLUSDT', 'TRXUSDT', 'DOTUSDT', 'MATICUSDT']
AMOUNT_OPTIONS = [50, 100, 500, 1000]  # USDT 金额选项

def is_authorized(user_id):
    return user_id == AUTHORIZED_USER_ID

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Calculate AHR999 Index", callback_data='calculate_ahr999')],
        [InlineKeyboardButton("Current Market Price", callback_data='market_price')],
        [InlineKeyboardButton("Place Order", callback_data='place_order')],
        [InlineKeyboardButton("Order Status", callback_data='order_status')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(bot, update):
    """发送欢迎消息和主菜单"""
    logger.info(f"User {update.effective_user.id} started the bot")
    await bot.send_message(
        chat_id=update.effective_chat.id,
        text='Welcome to the Crypto Trading Bot!\n\n'
             'Please select an option from the menu below:',
        reply_markup=get_main_menu_keyboard()
    )

async def button_callback(bot, update):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'calculate_ahr999':
        await calculate_ahr999_index(bot, query)
    elif query.data == 'market_price':
        await show_market_price(bot, query)
    elif query.data == 'place_order':
        await show_order_menu(bot, query)
    elif query.data == 'order_status':
        await show_order_status(bot, query)
    elif query.data == 'help':
        await show_help(bot, query)

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

        # 如果消息太长，分割它
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
        
        # 发送完数据后，显示主菜单
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
    if not is_authorized(query.from_user.id):
        await bot.answer_callback_query(query.id, text="You are not authorized to place orders.")
        return

    keyboard = [[InlineKeyboardButton(crypto, callback_data=f'symbol_{crypto}')] for crypto in TOP_CRYPTOS]
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Please select a trading pair:",
        reply_markup=reply_markup
    )

async def handle_symbol_selection(bot, query):
    symbol = query.data.split('_')[1]
    context.user_data['symbol'] = symbol
    
    keyboard = [
        [InlineKeyboardButton("BUY", callback_data='side_BUY')],
        [InlineKeyboardButton("SELL", callback_data='side_SELL')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=f"Selected pair: {symbol}\nPlease choose BUY or SELL:",
        reply_markup=reply_markup
    )

async def handle_side_selection(bot, query):
    side = query.data.split('_')[1]
    context.user_data['side'] = side
    
    keyboard = [[InlineKeyboardButton(f"{amount} USDT", callback_data=f'amount_{amount}')] for amount in AMOUNT_OPTIONS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=f"Selected: {context.user_data['symbol']} {side}\nPlease select the amount:",
        reply_markup=reply_markup
    )

async def handle_amount_selection(bot, query):
    amount = float(query.data.split('_')[1])
    context.user_data['amount'] = amount
    
    symbol = context.user_data['symbol']
    side = context.user_data['side']
    
    confirmation_text = (
        f"Order Summary:\n"
        f"Symbol: {symbol}\n"
        f"Side: {side}\n"
        f"Amount: {amount} USDT\n\n"
        f"Do you confirm this order?"
    )
    
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data='confirm_order')],
        [InlineKeyboardButton("Cancel", callback_data='cancel_order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=confirmation_text,
        reply_markup=reply_markup
    )

async def handle_order_confirmation(bot, query):
    if query.data == 'confirm_order':
        symbol = context.user_data['symbol']
        side = context.user_data['side']
        amount = context.user_data['amount']
        
        order = await trading_api.place_market_order(symbol, side, amount)
        if order:
            await bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"Order placed successfully!\nOrder ID: {order['orderId']}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="Failed to place the order. Please try again later.",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Order cancelled.",
            reply_markup=get_main_menu_keyboard()
        )
    
    context.user_data.clear()

async def show_order_status(bot, query):
    await bot.send_message(
        chat_id=query.message.chat_id,
        text="Order status functionality is not implemented yet.",
        reply_markup=get_main_menu_keyboard()
    )

async def show_help(bot, query):
    help_text = (
        "Welcome to the Crypto Trading Bot!\n\n"
        "Here are the available commands:\n"
        "- Calculate AHR999 Index: Get the current AHR999 index and investment advice\n"
        "- Current Market Price: Check current prices for top 10 cryptocurrencies\n"
        "- Place Order: (Coming soon) Place a new order\n"
        "- Order Status: (Coming soon) Check your order status\n"
        "- Help: Show this help message"
    )
    await bot.send_message(
        chat_id=query.message.chat_id,
        text=help_text,
        reply_markup=get_main_menu_keyboard()
    )

async def handle_message(bot, update):
    """处理所有文本消息，触发start功能"""
    logger.info(f"Received message from user {update.effective_user.id}: {update.message.text}")
    await start(bot, update)

async def process_update(bot, update):
    user_id = update.effective_user.id
    if update.message:
        if update.message.text == '/start':
            await start(bot, update)
        else:
            await handle_message(bot, update)
    elif update.callback_query:
        query = update.callback_query
        if query.data == 'place_order':
            await show_order_menu(bot, query)
        elif query.data.startswith('symbol_'):
            await handle_symbol_selection(bot, query)
        elif query.data.startswith('side_'):
            await handle_side_selection(bot, query)
        elif query.data.startswith('amount_'):
            await handle_amount_selection(bot, query)
        elif query.data in ['confirm_order', 'cancel_order']:
            await handle_order_confirmation(bot, query)
        else:
            await button_callback(bot, update)

async def main():
    """运行 Telegram 机器人"""
    await init_trading_api()
    bot = Bot(TOKEN)
    logger.info("Starting bot")
    
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

def run_bot():
    """启机器人的入口函数"""
    logger.info("Starting bot from run_bot function")
    asyncio.run(main())

def format_number(number, decimal_places=2):
    return f"{number:,.{decimal_places}f}"

if __name__ == '__main__':
    run_bot()
