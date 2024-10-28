import os
import sys

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到 Python 路径
sys.path.insert(0, current_dir)

from telegram_bot import run_bot

if __name__ == '__main__':
    run_bot()

