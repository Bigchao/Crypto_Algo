import os
import sys
import logging
from telegram_bot import run_bot

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        logger.info("Starting bot from main.py")
        run_bot()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        logger.error("Full error details:", exc_info=True)

