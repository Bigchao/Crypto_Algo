import logging
from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 使用 TOP_CRYPTOS 替代 COMMON_SYMBOLS
TOP_CRYPTOS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
    'DOGEUSDT', 'SOLUSDT', 'TRXUSDT', 'DOTUSDT', 'SHIBUSDT',
    'SUIUSDT', 'POLUSDT'
]

class OrderManagement:
    def __init__(self, api_key, api_secret):
        self.client = AsyncClient(api_key, api_secret)

    async def get_order_history(self, symbol=None):
        try:
            logger.info("Starting to fetch order history")
            all_orders = {}  # 使用字典来按币种组织订单
            current_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)

            # 如果指定了交易对，只获取该交易对的订单
            if symbol:
                symbols_to_check = [symbol]
            else:
                symbols_to_check = TOP_CRYPTOS  # 使用 TOP_CRYPTOS

            # 遍历每个交易对
            for sym in symbols_to_check:
                try:
                    logger.info(f"Fetching orders for {sym}")
                    # 获取过去24小时的订单
                    orders = await self.client.get_all_orders(
                        symbol=sym,
                        startTime=start_time,
                        endTime=current_time
                    )
                    
                    if orders:  # 只添加有订单的交易对
                        # 按时间排序，最新的订单在前
                        orders.sort(key=lambda x: x['time'], reverse=True)
                        all_orders[sym] = orders
                        logger.info(f"Successfully fetched {len(orders)} orders for {sym}")
                    
                except BinanceAPIException as e:
                    logger.warning(f"Error fetching orders for {sym}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error fetching orders for {sym}: {e}")
                    continue

            if all_orders:
                logger.info(f"Successfully fetched orders for {len(all_orders)} symbols")
                return all_orders
            else:
                logger.info("No orders found in the last 24 hours")
                return {}

        except BinanceAPIException as e:
            logger.error(f"Error fetching order history: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_order_history: {e}")
            return {}