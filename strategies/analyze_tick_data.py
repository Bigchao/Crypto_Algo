import pandas as pd
import os
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TickDataAnalyzer:
    def __init__(self):
        self.data_folder = 'tick_data'
        self.file_name = 'BTCUSDT_all_tick_data.h5'
        self.file_path = os.path.join(self.data_folder, self.file_name)

    def analyze_data(self):
        """分析HDF5文件中的交易数据"""
        try:
            logger.info(f"开始分析文件: {self.file_path}")
            
            # 读取HDF5文件
            df = pd.read_hdf(self.file_path, key='trades')
            
            # 基本信息
            total_rows = len(df)
            start_time = df['time'].min()
            end_time = df['time'].max()
            time_span = end_time - start_time
            
            # 输出分析结果
            logger.info("\n=== 数据分析报告 ===")
            logger.info(f"总记录数: {total_rows:,} 条")
            logger.info(f"数据时间范围: 从 {start_time} 到 {end_time}")
            logger.info(f"总计时间跨度: {time_span}")
            
            return {
                'total_rows': total_rows,
                'start_time': start_time,
                'end_time': end_time,
                'time_span': time_span
            }
            
        except FileNotFoundError:
            logger.error(f"文件未找到: {self.file_path}")
            return None
        except Exception as e:
            logger.error(f"分析过程中出错: {str(e)}")
            return None

if __name__ == "__main__":
    analyzer = TickDataAnalyzer()
    analysis_results = analyzer.analyze_data()
    
    if analysis_results:
        logger.info("\n分析完成!")