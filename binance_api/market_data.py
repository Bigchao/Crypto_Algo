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
            volume_usdt = volume * price  # Convert volume to USDT
            
            logger.info(f"Calculated volume for {item['symbol']}: {volume_usdt} USDT")
            
            formatted_item = {
                'symbol': item['symbol'],
                'price': price,
                'change': float(item['priceChangePercent']),
                'high': float(item['highPrice']),
                'low': float(item['lowPrice']),
                'volume': volume_usdt
            }
            formatted_data.append(formatted_item)
        except (KeyError, ValueError) as e:
            logger.error(f"Error formatting data for {item.get('symbol', 'Unknown')}: {e}")
    
    return formatted_data
