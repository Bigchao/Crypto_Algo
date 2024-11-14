import logging
import os
import sys
import pandas as pd
import backtrader as bt
from datetime import datetime

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from strategies.hedge_strategy import SpotFuturesHedgeStrategy

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HDF5CSVData(bt.feeds.PandasData):
    """自定义数据加载类"""
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )

def load_data():
    """加载现货和合约数据"""
    try:
        # 加载现货数据
        spot_file = os.path.join(project_root, 'kline_data', 'BTCUSDT_4h_klines.h5')
        spot_df = pd.read_hdf(spot_file, key='klines')
        spot_df.set_index('timestamp', inplace=True)
        
        # 加载合约数据
        futures_file = os.path.join(project_root, 'futures_data', 'BTCUSDT_4h_futures.h5')
        futures_df = pd.read_hdf(futures_file, key='futures_klines')
        futures_df.set_index('timestamp', inplace=True)
        
        # 加载资金费率数据
        funding_file = os.path.join(project_root, 'futures_data', 'BTCUSDT_funding_rates.h5')
        funding_df = pd.read_hdf(funding_file, key='funding_rates')
        
        # 对齐数据的时间索引
        common_index = spot_df.index.intersection(futures_df.index)
        spot_df = spot_df.loc[common_index]
        futures_df = futures_df.loc[common_index]
        
        # 将资金费率数据重采样并对齐到K线数据
        funding_df = funding_df.reindex(common_index, method='ffill')
        
        # 确保资金费率数据完整
        if funding_df['fundingRate'].isnull().any():
            logger.warning("存在缺失的资金费率数据，使用0填充")
            funding_df['fundingRate'] = funding_df['fundingRate'].fillna(0)
        
        logger.info(f"数据时间范围: {common_index[0]} 到 {common_index[-1]}")
        logger.info(f"总数据点数: {len(common_index)}")
        logger.info(f"平均资金费率: {funding_df['fundingRate'].mean():.6%}")
        logger.info(f"最大资金费率: {funding_df['fundingRate'].max():.6%}")
        logger.info(f"最小资金费率: {funding_df['fundingRate'].min():.6%}")
        
        return spot_df, futures_df, funding_df
        
    except Exception as e:
        logger.error(f"加载数据时出错: {str(e)}")
        return None, None, None

def run_backtest():
    """运行回测"""
    try:
        # 创建回测引擎
        cerebro = bt.Cerebro()
        
        # 加载数据
        spot_df, futures_df, funding_df = load_data()
        if spot_df is None or futures_df is None or funding_df is None:
            return
            
        # 添加数据到回测引擎
        spot_data = HDF5CSVData(dataname=spot_df)
        futures_data = HDF5CSVData(dataname=futures_df)
        funding_data = bt.feeds.PandasData(
            dataname=funding_df[['fundingRate']],
            datetime=None,
            openinterest=None
        )
        
        cerebro.adddata(spot_data, name='spot')
        cerebro.adddata(futures_data, name='futures')
        cerebro.adddata(funding_data, name='funding')
        
        # 设置初始资金
        initial_cash = 100000.0
        cerebro.broker.setcash(initial_cash)
        
        # 设置手续费
        cerebro.broker.setcommission(commission=0.001)  # 0.1% 手续费
        
        # 添加策略
        cerebro.addstrategy(SpotFuturesHedgeStrategy,
                           hedge_ratio=0.8,
                           funding_threshold=0.001,
                           position_size=1.0,
                           leverage=3)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 打印初始资金
        logger.info(f'初始资金: {initial_cash:.2f}')
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 打印最终资金
        final_value = cerebro.broker.getvalue()
        logger.info(f'最终资金: {final_value:.2f}')
        logger.info(f'总收益率: {((final_value - initial_cash) / initial_cash * 100):.2f}%')
        
        # 打印分析结果
        logger.info('\n=== 策略表现分析 ===')
        logger.info(f'夏普比率: {strat.analyzers.sharpe.get_analysis()["sharperatio"]:.2f}')
        logger.info(f'最大回撤: {strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]:.2f}%')
        logger.info(f'年化收益率: {strat.analyzers.returns.get_analysis()["rnorm100"]:.2f}%')
        
        # 交易统计
        trade_analysis = strat.analyzers.trades.get_analysis()
        logger.info('\n=== 交易统计 ===')
        logger.info(f'总交易次数: {trade_analysis["total"]["total"]}')
        if trade_analysis["total"]["total"] > 0:
            logger.info(f'盈利交易次数: {trade_analysis["won"]["total"]}')
            logger.info(f'亏损交易次数: {trade_analysis["lost"]["total"]}')
            win_rate = trade_analysis["won"]["total"] / trade_analysis["total"]["total"]
            logger.info(f'胜率: {win_rate*100:.2f}%')
        
        # 绘制图表
        cerebro.plot()
        
    except Exception as e:
        logger.error(f"回测过程中出错: {str(e)}")
        logger.error("详细错误信息:", exc_info=True)

if __name__ == "__main__":
    run_backtest() 