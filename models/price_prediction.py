import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
root_dir = os.path.dirname(current_dir)
# 将项目根目录添加到 Python 路径
sys.path.insert(0, root_dir)

import config
from binance.client import Client
from dotenv import load_dotenv
import asyncio
from binance import AsyncClient

# 加载环境变量
load_dotenv()

# 初始化Binance客户端
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'))

def load_parameters():
    params_df = pd.read_json(config.PARAMS_FILE, encoding='utf-8')
    return params_df.set_index('parameter')['value'].to_dict()

def predict_price(days_since_start):
    params = load_parameters()
    r = params['r']
    X0 = params['X0']
    return config.X_M / (1 + (config.X_M/X0 - 1) * np.exp(-r * days_since_start))

async def get_current_price():
    client = await AsyncClient.create()
    ticker = await client.get_symbol_ticker(symbol="BTCUSDT")
    await client.close_connection()
    return float(ticker['price'])

async def calculate_ahr999():
    # 读取模型参数
    params = load_parameters()
    print(f"模型参数: {params}")
    
    # 获取实时价格
    current_price = await get_current_price()
    print(f"当前价格: {current_price}")
    
    # 获取历史价格数据
    df = get_historical_prices()
    print(f"历史数据形状: {df.shape}")
    
    last_fit_date = datetime.strptime(params['last_fit_date'], '%Y-%m-%d')
    print(f"最后拟合日期: {last_fit_date}")
    
    # 修正：使用比特币实际开始日期计算天数
    btc_start_date = datetime.strptime(config.BTC_START_DATE, '%Y-%m-%d')
    days_since_start = (datetime.now() - btc_start_date).days
    print(f"自比特币开始以来的天数: {days_since_start}")
    
    # 修正：计算最近200天的平均价格
    avg_price_200d = df['close'].tail(200).mean()
    print(f"200天平均价格: {avg_price_200d}")
    
    predicted_price = predict_price(days_since_start)
    print(f"预测价格: {predicted_price}")
    
    ahr999 = (current_price / avg_price_200d) * (current_price / predicted_price)
    print(f"计算得到的AHR999: {ahr999}")
    
    return ahr999, datetime.now()

def get_historical_prices():
    end_time = datetime.now()
    start_time = end_time - timedelta(days=200)
    klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, start_time.strftime("%d %b %Y %H:%M:%S"), end_time.strftime("%d %b %Y %H:%M:%S"))
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

if __name__ == "__main__":
    ahr999, timestamp = asyncio.run(calculate_ahr999())
    print(f"AHR999: {ahr999:.4f}")
    print(f"Timestamp: {timestamp}")

    # 将结果保存到CSV文件
    result_df = pd.DataFrame({'Date': [timestamp.date()], 'Time': [timestamp.time()], 'AHR999': [ahr999]})
    result_df.to_csv(config.AHR999_FILE, mode='a', header=False, index=False)
    print(f"结果已追加到 {config.AHR999_FILE}")