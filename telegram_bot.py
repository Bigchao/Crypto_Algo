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

async def start(bot, update):
    """发送欢迎消息和功能按钮"""
    logger.info(f"User {update.effective_user.id} started the bot")
    keyboard = [
        [InlineKeyboardButton("Calculate AHR999 Index", callback_data='calculate_ahr999')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(
        chat_id=update.effective_chat.id,
        text='Welcome to the AHR999 Index Calculator!\n\n'
             'Click the button below to calculate the AHR999 Index:',
        reply_markup=reply_markup
    )

async def button_callback(bot, update):
    """处理按钮点击事件"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"User {query.from_user.id} clicked the button")
    
    try:
        ahr999_value, timestamp = await calculate_ahr999()
        current_price = await get_current_price()
        
        investment_advice = get_investment_advice(ahr999_value)  # 获取投资建议
        
        ahr999_message = (
            f"BTC当前价格: ${current_price:.2f}\n"
            f"AHR999指数: {ahr999_value:.4f}\n"
            f"计算时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"投资建议: {investment_advice}"  # 添加投资建议到消息中
        )
        
        keyboard = [
            [InlineKeyboardButton("再次计算", callback_data='calculate_ahr999')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=query.message.chat_id,
            text=ahr999_message,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"计算AHR999时发生错误: {str(e)}")
        await bot.send_message(
            chat_id=query.message.chat_id,
            text="抱歉，计算AHR999指数或获取BTC价格时出现错误。请稍后再试。"
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