import logging
import os
import pandas as pd
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class BTCTickData:
    def __init__(self, api_key, api_secret):
        self.client = AsyncClient(api_key, api_secret)
        self.symbol = 'BTCUSDT'
        self.data_folder = 'tick_data'

    async def fetch_and_save_trades(self, start_id, end_id, batch_size=1000):
        """获取并保存指定范围内的交易数据"""
        try:
            trades = await self.client.get_historical_trades(
                symbol=self.symbol,
                fromId=start_id,
                limit=batch_size
            )
            if trades:
                self.save_trades_to_hdf5(trades)
            return trades
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return []

    def save_trades_to_hdf5(self, trades):
        """保存交易数据到HDF5文件"""
        filename = f"{self.symbol}_all_tick_data.h5"
        filepath = os.path.join(self.data_folder, filename)
        
        df = pd.DataFrame(trades)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        
        # 使用 HDF5 格式保存
        df.to_hdf(filepath, key='trades', mode='a', format='table', append=True)
        logger.info(f"Saved {len(trades)} trades to {filepath}")

    async def run(self, start_id, end_id, batch_size=1000):
        """异步获取交易数据"""
        tasks = []
        for start in range(start_id, end_id, batch_size):
            tasks.append(self.fetch_and_save_trades(start, start + batch_size, batch_size))
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    
    btc_data = BTCTickData(api_key, api_secret)
    asyncio.run(btc_data.run(start_id=1, end_id=1000000))  # 示例：获取ID从1到1000000的交易数据