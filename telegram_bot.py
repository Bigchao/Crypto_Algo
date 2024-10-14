import logging
import os
import asyncio
from time import sleep
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError

from models.price_prediction import calculate_ahr999, get_current_price
from models.investment_advice import get_investment_advice  # 新增这行

# 加载环境变量
load_dotenv()

# 设置你的bot token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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
    # 保留现有的 AHR999 计算逻辑
    try:
        ahr999_value, timestamp = await calculate_ahr999()
        current_price = await get_current_price()
        
        investment_advice = get_investment_advice(ahr999_value)
        
        ahr999_message = (
            f"BTC当前价格: ${current_price:.2f}\n"
            f"AHR999指数: {ahr999_value:.4f}\n"
            f"计算时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"投资建议: {investment_advice}"
        )
        
        await bot.send_message(
            chat_id=query.message.chat_id,
            text=ahr999_message,
            reply_markup=get_main_menu_keyboard()  # 返回主菜单
        )
    except Exception as e:
        logger.error(f"计算AHR999时发生错误: {str(e)}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="抱歉，计算AHR999指数或获取BTC价格时出现错误。请稍后再试。",
            reply_markup=get_main_menu_keyboard()  # 返回主菜单
        )

async def show_market_price(bot, query):
    try:
        current_price = await get_current_price()
        await bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Current BTC price: ${current_price:.2f}",
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
    await bot.send_message(
        chat_id=query.message.chat_id,
        text="Order functionality is not implemented yet.",
        reply_markup=get_main_menu_keyboard()
    )

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
        "- Current Market Price: Check the current BTC price\n"
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
    if update.message:
        if update.message.text == '/start':
            await start(bot, update)
        else:
            await handle_message(bot, update)
    elif update.callback_query:
        await button_callback(bot, update)

async def main():
    """运行 Telegram 机器人"""
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
    """启动机器人的入口函数"""
    logger.info("Starting bot from run_bot function")
    asyncio.run(main())

if __name__ == '__main__':
    run_bot()
