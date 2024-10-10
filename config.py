import os
import config

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
OUTPUT_DATA_DIR = os.path.join(DATA_DIR, 'output')

# 图表目录
CHARTS_DIR = os.path.join(ROOT_DIR, 'charts')

# 日志目录
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')

# 确保这些目录存在
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DATA_DIR, CHARTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 更新文件路径
AHR999_FILE = os.path.join(OUTPUT_DATA_DIR, 'ahr999_output.csv')
PARAMS_FILE = os.path.join(PROCESSED_DATA_DIR, 'model_params.json')

X0 = 0.04951 
X_M = 100000  
INITIAL_R = 0.002985  # Updated by model_fitting.py
DATA_FILE = os.path.join(RAW_DATA_DIR, 'bitcoin_historical_data.csv')
PARAMS_FILE = 'model_params.json'
AHR999_FILE = 'ahr999_output.csv'
BTC_START_DATE = '2010-07-17'
