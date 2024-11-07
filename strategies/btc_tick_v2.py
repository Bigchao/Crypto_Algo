import logging
import os
import pandas as pd
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from datetime import datetime
import asyncio
import aiohttp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class BTCTickData:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        self.symbol = 'BTCUSDT'
        self.data_folder = 'tick_data'

    async def initialize(self):
        """初始化 Binance 客户端"""
        try:
            self.client = await AsyncClient.create(self.api_key, self.api_secret)
            logger.info("Binance client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            return False

    async def close(self):
        """关闭客户端连接"""
        if self.client:
            await self.client.close_connection()

    async def fetch_and_save_trades(self, start_id, end_id, batch_size=1000):
        """获取并保存指定范围内的交易数据"""
        try:
            logger.info(f"[fetch_and_save_trades] Starting fetch for ID range: {start_id} to {end_id}")
            logger.info(f"[fetch_and_save_trades] Batch size: {batch_size}")
            
            trades = await self.client.get_historical_trades(
                symbol=self.symbol,
                fromId=start_id,
                limit=batch_size
            )
            
            if trades:
                logger.info(f"[fetch_and_save_trades] Successfully fetched {len(trades)} trades")
                logger.info(f"[fetch_and_save_trades] First trade ID: {trades[0]['id']}")
                logger.info(f"[fetch_and_save_trades] Last trade ID: {trades[-1]['id']}")
                
                # 转换时间戳为可读格式
                first_trade_time = datetime.fromtimestamp(trades[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')
                last_trade_time = datetime.fromtimestamp(trades[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"[fetch_and_save_trades] Time range: from {first_trade_time} to {last_trade_time}")
                
                self.save_trades_to_hdf5(trades)
                return trades
            else:
                logger.warning(f"[fetch_and_save_trades] No trades found for ID range {start_id} to {end_id}")
                return []
                
        except asyncio.TimeoutError:
            logger.error(f"[fetch_and_save_trades] Timeout error for ID range {start_id} to {end_id}")
            logger.error("[fetch_and_save_trades] Waiting before retry...")
            await asyncio.sleep(5)  # 添加延迟
            return []
        except BinanceAPIException as e:
            logger.error(f"[fetch_and_save_trades] Binance API error: {e}")
            logger.error(f"[fetch_and_save_trades] Error code: {e.code}")
            logger.error(f"[fetch_and_save_trades] Error message: {e.message}")
            return []
        except Exception as e:
            logger.error(f"[fetch_and_save_trades] Unexpected error: {str(e)}")
            logger.error("[fetch_and_save_trades] Full error details:", exc_info=True)
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
        try:
            logger.info(f"[run] Starting data collection from ID {start_id} to {end_id}")
            logger.info(f"[run] Using batch size: {batch_size}")
            
            if not await self.initialize():
                logger.error("[run] Failed to initialize client")
                return False

            tasks = []
            total_batches = (end_id - start_id) // batch_size
            completed_batches = 0
            logger.info(f"[run] Total number of batches to process: {total_batches}")
            
            for start in range(start_id, end_id, batch_size):
                try:
                    logger.info(f"[run] Creating task for batch starting at ID {start}")
                    tasks.append(self.fetch_and_save_trades(start, start + batch_size, batch_size))
                    
                    # 每10个任务处理一次，避免并发请求过多
                    if len(tasks) >= 10:
                        logger.info("[run] Processing batch of 10 tasks")
                        try:
                            await asyncio.gather(*tasks)
                            completed_batches += len(tasks)
                            progress = (completed_batches / total_batches) * 100
                            logger.info(f"[run] Progress: {progress:.2f}% ({completed_batches}/{total_batches} batches)")
                        except Exception as e:
                            logger.error(f"[run] Error processing batch: {e}")
                            # 继续执行，不终止程序
                            
                        tasks = []
                        logger.info("[run] Waiting before next batch...")
                        await asyncio.sleep(1)  # 添加延迟
                
                except Exception as batch_error:
                    logger.error(f"[run] Error creating batch task: {batch_error}")
                    continue  # 继续处理下一个批次
            
            # 处理剩余的任务
            if tasks:
                try:
                    logger.info(f"[run] Processing remaining {len(tasks)} tasks")
                    await asyncio.gather(*tasks)
                    completed_batches += len(tasks)
                    logger.info(f"[run] Final progress: {(completed_batches / total_batches) * 100:.2f}%")
                except Exception as e:
                    logger.error(f"[run] Error processing final batch: {e}")
            
            logger.info("[run] Data collection completed!")
            return True
            
        except Exception as e:
            logger.error(f"[run] Error in run method: {str(e)}")
            logger.error("[run] Full error details:", exc_info=True)
            return False
        finally:
            await self.close()
            logger.info("[run] Client connection closed")

async def main():
    """主函数"""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    
    btc_data = BTCTickData(api_key, api_secret)
    await btc_data.run(start_id=1, end_id=1000000)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())