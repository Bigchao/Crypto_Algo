import logging
from binance.client import AsyncClient
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOP_CRYPTOS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 
                'DOGEUSDT', 'SOLUSDT', 'TRXUSDT', 'DOTUSDT', 'MATICUSDT']

async def get_top_crypto_data():
    client = await AsyncClient.create()
    tasks = [client.get_ticker(symbol=symbol) for symbol in TOP_CRYPTOS]
    results = await asyncio.gather(*tasks)
    await client.close_connection()
    
    for result in results:
        logger.info(f"Raw API response for {result['symbol']}: {result}")
    
    return results

async def format_crypto_data(data):
    formatted_data = []
    for item in data:
        try:
            volume = float(item['volume'])
            price = float(item['lastPrice'])
            price_change = float(item['priceChange'])
            price_change_percent = float(item['priceChangePercent'])
            volume_usdt = volume * price  # Convert volume to USDT
            
            logger.info(f"Data for {item['symbol']}:")
            logger.info(f"  Price: {price}")
            logger.info(f"  Price Change: {price_change}")
            logger.info(f"  Price Change Percent: {price_change_percent}%")
            logger.info(f"  Volume: {volume}")
            logger.info(f"  Volume in USDT: {volume_usdt}")
            
            formatted_item = {
                'symbol': item['symbol'],
                'price': price,
                'change': price_change_percent,
                'high': float(item['highPrice']),
                'low': float(item['lowPrice']),
                'volume': volume_usdt
            }
            formatted_data.append(formatted_item)
        except (KeyError, ValueError) as e:
            logger.error(f"Error formatting data for {item.get('symbol', 'Unknown')}: {e}")
    
    return formatted_data
