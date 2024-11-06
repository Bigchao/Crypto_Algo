import logging
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv
import asyncio

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class TurtleTrading:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.client = None
        self.symbol = 'BTCUSDT'
        self.data_folder = 'historical_data'
        
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
        
    async def get_historical_klines(self):
        """获取BTCUSDT的历史K线数据并保存为CSV"""
        try:
            logger.info(f"Fetching historical klines for {self.symbol}")
            
            # 获取最早的可用数据
            klines = await self.client.get_historical_klines(
                symbol=self.symbol,
                interval='1d',  # 日线数据
                start_str="2017-08-17",  # BTCUSDT 在 Binance 上市的大致时间
            )
            
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
            
            # 生成文件名（包含当前时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.symbol}_historical_data_{timestamp}.csv"
            filepath = os.path.join(self.data_folder, filename)
            
            # 保存为CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Successfully saved {len(df)} records to {filepath}")
            
            # 打印数据统计信息
            logger.info(f"Data summary:")
            logger.info(f"Date range: from {df['timestamp'].min()} to {df['timestamp'].max()}")
            logger.info(f"Total trading days: {len(df)}")
            logger.info(f"Price range: {df['low'].min():.2f} - {df['high'].max():.2f} USDT")
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
        finally:
            if self.client:
                await self.client.close_connection()
                
    async def get_historical_trades(self):
        """获取BTCUSDT的历史逐笔交易数据"""
        try:
            logger.info(f"Fetching historical trades for {self.symbol}")
            all_trades = []
            
            # 获取最近的成交ID作为起点
            trades = await self.client.get_historical_trades(
                symbol=self.symbol,
                limit=1000  # 每次获取1000条记录
            )
            
            if trades:
                from_id = trades[0]['id']  # 获取最早的交易ID
                
                while True:
                    trades = await self.client.get_historical_trades(
                        symbol=self.symbol,
                        limit=1000,
                        fromId=from_id
                    )
                    
                    if not trades:
                        break
                        
                    all_trades.extend(trades)
                    logger.info(f"Fetched {len(trades)} trades, total: {len(all_trades)}")
                    
                    # 更新fromId为最早的交易ID
                    from_id = trades[-1]['id'] - 1000
                    
                    # 保存中间结果
                    if len(all_trades) % 10000 == 0:
                        self._save_trades_to_csv(all_trades[-10000:], append=True)
                    
            return all_trades
                
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def _save_trades_to_csv(self, trades, append=False):
        """保存交易数据到CSV文件"""
        mode = 'a' if append else 'w'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.symbol}_trades_{timestamp}.csv"
        filepath = os.path.join(self.data_folder, filename)
        
        df = pd.DataFrame(trades)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        
        df.to_csv(filepath, mode=mode, index=False)
        logger.info(f"Saved {len(trades)} trades to {filepath}")

async def main():
    """主函数"""
    turtle = TurtleTrading()
    
    # 初始化
    if await turtle.initialize():
        # 获取历史数据
        df = await turtle.get_historical_klines()
        if df is not None:
            logger.info("Data retrieval completed successfully")
        else:
            logger.error("Failed to retrieve historical data")
    else:
        logger.error("Failed to initialize TurtleTrading")

if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行主函数
    asyncio.run(main())
