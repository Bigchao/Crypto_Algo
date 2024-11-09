import logging
import os
import pandas as pd
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from datetime import datetime
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class BTC4HKlines:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.client = None
        self.symbol = 'BTCUSDT'
        self.interval = '4h'
        self.data_folder = 'kline_data'
        
    async def initialize(self):
        """初始化 Binance 客户端"""
        try:
            self.client = await AsyncClient.create(self.api_key, self.api_secret)
            logger.info("Binance client initialized successfully")
            
            # 创建数据文件夹（如果不存在）
            if not os.path.exists(self.data_folder):
                os.makedirs(self.data_folder)
                logger.info(f"Created data folder: {self.data_folder}")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            return False

    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.close_connection()

    async def fetch_klines(self):
        """获取所有4小时K线数据"""
        try:
            logger.info(f"Fetching 4h klines for {self.symbol}")
            
            # 获取最早的可用数据
            klines = await self.client.get_historical_klines(
                symbol=self.symbol,
                interval=self.interval,
                start_str="2017-08-17",  # BTCUSDT 在 Binance 上市的大致时间
            )
            
            if klines:
                logger.info(f"Successfully fetched {len(klines)} klines")
                self.save_klines_to_hdf5(klines)
                return klines
            else:
                logger.warning("No klines data found")
                return []
                
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def save_klines_to_hdf5(self, klines):
        """保存K线数据到HDF5文件"""
        try:
            filename = f"{self.symbol}_4h_klines.h5"
            filepath = os.path.join(self.data_folder, filename)
            
            # 将数据转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'close_time', 'quote_asset_volume',
                'number_of_trades', 'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # 转换数值类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                             'quote_asset_volume', 'taker_buy_base_asset_volume',
                             'taker_buy_quote_asset_volume']
            
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 保存为HDF5格式
            df.to_hdf(filepath, key='klines', mode='w')
            
            # 打印数据统计信息
            logger.info(f"Data summary:")
            logger.info(f"Date range: from {df['timestamp'].min()} to {df['timestamp'].max()}")
            logger.info(f"Total periods: {len(df)}")
            logger.info(f"Price range: {df['low'].min():.2f} - {df['high'].max():.2f} USDT")
            
        except Exception as e:
            logger.error(f"Error saving klines to HDF5: {e}")

async def main():
    """主函数"""
    klines = BTC4HKlines()
    
    if await klines.initialize():
        await klines.fetch_klines()
        await klines.close()
    else:
        logger.error("Failed to initialize")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 