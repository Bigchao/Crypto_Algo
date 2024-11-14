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

class BinanceFuturesData:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.client = None
        self.data_folder = 'futures_data'
        
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

    async def fetch_all_futures_klines(self, symbol, interval, start_str="2019-09-01"):
        """获取所有合约K线数据，从指定日期开始"""
        try:
            logger.info(f"Fetching all futures klines for {symbol} from {start_str}")
            all_klines = []
            
            # 转换开始时间为时间戳
            start_ts = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
            end_ts = int(datetime.now().timestamp() * 1000)
            
            while start_ts < end_ts:
                # 获取一批数据
                klines = await self.client.futures_klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=start_ts,
                    limit=1500
                )
                
                if not klines:
                    break
                    
                all_klines.extend(klines)
                logger.info(f"Fetched {len(klines)} klines, total: {len(all_klines)}")
                
                # 更新开始时间戳为最后一条数据的时间
                start_ts = klines[-1][0] + 1
                
                # 添加延迟避免触发频率限制
                await asyncio.sleep(0.5)
            
            if all_klines:
                self.save_klines_to_hdf5(all_klines, symbol, interval)
                logger.info(f"Total klines saved: {len(all_klines)}")
                
            return all_klines
                
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def save_klines_to_hdf5(self, klines, symbol, interval):
        """保存K线数据到HDF5文件"""
        try:
            filename = f"{symbol}_{interval}_futures.h5"
            filepath = os.path.join(self.data_folder, filename)
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'close_time', 'quote_volume',
                'trades_count', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # 转换数值类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                             'quote_volume', 'taker_buy_volume',
                             'taker_buy_quote_volume']
            
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 保存到HDF5
            df.to_hdf(filepath, key='futures_klines', mode='w')
            logger.info(f"Saved {len(df)} klines to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving klines to HDF5: {e}")

    async def fetch_funding_rates(self, symbol, start_str=None):
        """获取资金费率数据"""
        try:
            rates = await self.client.futures_funding_rate(
                symbol=symbol,
                startTime=start_str,
                limit=1000
            )
            return rates
        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
            return []

    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.close_connection()

async def main():
    """主函数"""
    futures_data = BinanceFuturesData()
    
    if await futures_data.initialize():
        # 获取BTC永续合约数据
        symbol = 'BTCUSDT'
        interval = '4h'
        
        # 获取从2019年9月开始的所有数据（BTCUSDT永续合约上线时间）
        await futures_data.fetch_all_futures_klines(
            symbol=symbol, 
            interval=interval,
            start_str="2019-09-01"  # BTCUSDT永续合约开始时间
        )
        
        # 获取资金费率
        funding_rates = await futures_data.fetch_funding_rates(symbol)
        if funding_rates:
            logger.info(f"Fetched {len(funding_rates)} funding rate records")
        
        await futures_data.close()
    else:
        logger.error("Failed to initialize")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 