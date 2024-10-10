from binance.client import AsyncClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class TradingAPI:
    def __init__(self):
        self.client = None

    async def init(self):
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.client = await AsyncClient.create(api_key, api_secret)
        print("Binance trading API initialized")

    async def close(self):
        if self.client:
            await self.client.close_connection()

    # 这里可以添加其他交易相关的方法

trading = TradingAPI()

async def init():
    await trading.init()

# 其他交易相关的函数可以在这里定义
