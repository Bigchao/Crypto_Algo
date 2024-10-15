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

    async def place_market_order(self, symbol, side, amount):
        try:
            if side == 'BUY':
                order = await self.client.order_market_buy(
                    symbol=symbol,
                    quoteOrderQty=amount  # 使用 quoteOrderQty 来指定 USDT 金额
                )
            else:  # SELL
                # 对于卖出，我们需要先获取当前价格来计算数量
                ticker = await self.client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                quantity = amount / current_price
                order = await self.client.order_market_sell(
                    symbol=symbol,
                    quantity=quantity
                )
            return order
        except Exception as e:
            print(f"Error placing market order: {e}")
            return None

trading_api = TradingAPI()

async def init_trading_api():
    await trading_api.init()

# 其他交易相关的函数可以在这里定义
