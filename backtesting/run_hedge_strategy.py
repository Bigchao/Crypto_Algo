import logging
import os
import sys
import pandas as pd
import backtrader as bt
from datetime import datetime
import numpy as np

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
        spot_df['timestamp'] = pd.to_datetime(spot_df['timestamp'], unit='ms')
        spot_df.set_index('timestamp', inplace=True)
        
        # 加载合约数据
        futures_file = os.path.join(project_root, 'futures_data', 'BTCUSDT_4h_futures.h5')
        futures_df = pd.read_hdf(futures_file, key='futures_klines')
        futures_df['timestamp'] = pd.to_datetime(futures_df['timestamp'], unit='ms')
        futures_df.set_index('timestamp', inplace=True)
        
        # 加载资金费率数据
        funding_file = os.path.join(project_root, 'futures_data', 'BTCUSDT_funding_rates.h5')
        funding_df = pd.read_hdf(funding_file, key='funding_rates')
        
        # 打印资金费率数据的描述统计
        logger.info("\n=== 资金费率数据描述 ===")
        logger.info("原始资金费率数据形状: {}".format(funding_df.shape))
        logger.info("资金费率数据列名: {}".format(funding_df.columns.tolist()))
        logger.info("\n资金费率统计描述:")
        logger.info(funding_df['fundingRate'].describe().to_string())
        logger.info("\n资金费率数据前5行:")
        logger.info(funding_df.head().to_string())
        logger.info("\n资金费率数据后5行:")
        logger.info(funding_df.tail().to_string())
        
        # 确保资金费率数据的时间索引格式正确
        if 'fundingTime' in funding_df.columns:
            funding_df['fundingTime'] = pd.to_datetime(funding_df['fundingTime'])
            funding_df.set_index('fundingTime', inplace=True)
        
        # 对齐数据的时间索引
        common_index = spot_df.index.intersection(futures_df.index)
        spot_df = spot_df.loc[common_index]
        futures_df = futures_df.loc[common_index]
        
        # 将资金费率数据重采样到4小时并对齐
        funding_df = funding_df.resample('4H').ffill()
        funding_df = funding_df.reindex(common_index)
        
        # 确保数据完整性
        spot_df = spot_df.fillna(method='ffill')
        futures_df = futures_df.fillna(method='ffill')
        funding_df = funding_df.fillna(0)  # 将缺失的资金费率填充为0
        
        # 移除包含无限值的行
        spot_df = spot_df.replace([np.inf, -np.inf], np.nan).dropna()
        futures_df = futures_df.replace([np.inf, -np.inf], np.nan).dropna()
        funding_df = funding_df.replace([np.inf, -np.inf], np.nan).dropna()
        
        # 再次对齐数据
        common_index = spot_df.index.intersection(futures_df.index).intersection(funding_df.index)
        spot_df = spot_df.loc[common_index]
        futures_df = futures_df.loc[common_index]
        funding_df = funding_df.loc[common_index]
        
        logger.info(f"数据时间范围: {common_index[0]} 到 {common_index[-1]}")
        logger.info(f"总数据点数: {len(common_index)}")
        logger.info(f"平均资金费率: {funding_df['fundingRate'].mean():.6%}")
        logger.info(f"最大资金费率: {funding_df['fundingRate'].max():.6%}")
        logger.info(f"最小资金费率: {funding_df['fundingRate'].min():.6%}")
        
        return spot_df, futures_df, funding_df
        
    except Exception as e:
        logger.error(f"加载数据时出错: {str(e)}")
        logger.error("详细错误信息:", exc_info=True)
        return None, None, None

def run_backtest():
    """运行回测"""
    try:
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
            openinterest=None,
            volume=None
        )
        
        cerebro.adddata(spot_data, name='spot')
        cerebro.adddata(futures_data, name='futures')
        cerebro.adddata(funding_data, name='funding')
        
        # 设置初始资金
        initial_cash = 100000.0
        cerebro.broker.setcash(initial_cash)
        
        # 设置手续费
        cerebro.broker.setcommission(commission=0.001)
        
        # 添加策略
        cerebro.addstrategy(SpotFuturesHedgeStrategy)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 打印结果
        final_value = cerebro.broker.getvalue()
        logger.info(f'最终资金: {final_value:.2f}')
        logger.info(f'总收益率: {((final_value - initial_cash) / initial_cash * 100):.2f}%')
        
        # 打印分析结果
        logger.info('\n=== 策略表现分析 ===')
        sharpe = strat.analyzers.sharpe.get_analysis()
        if sharpe.get('sharperatio'):
            logger.info(f'夏普比率: {sharpe["sharperatio"]:.2f}')
        else:
            logger.info('夏普比率: N/A')
            
        drawdown = strat.analyzers.drawdown.get_analysis()
        if drawdown.get('max'):
            logger.info(f'最大回撤: {drawdown["max"]["drawdown"]:.2f}%')
        else:
            logger.info('最大回撤: N/A')
            
        returns = strat.analyzers.returns.get_analysis()
        if returns.get('rnorm100'):
            logger.info(f'年化收益率: {returns["rnorm100"]:.2f}%')
        else:
            logger.info('年化收益率: N/A')
        
        # 交易统计
        trades = strat.analyzers.trades.get_analysis()
        logger.info('\n=== 交易统计 ===')
        total_trades = trades.get('total', {}).get('total', 0)
        logger.info(f'总交易次数: {total_trades}')
        
        if total_trades > 0:
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            logger.info(f'盈利交易次数: {won_trades}')
            logger.info(f'亏损交易次数: {lost_trades}')
            win_rate = won_trades / total_trades * 100 if total_trades > 0 else 0
            logger.info(f'胜率: {win_rate:.2f}%')
        
        # 尝试绘图，如果失败则跳过
        try:
            figs = cerebro.plot(style='candlestick', barup='green', bardown='red', 
                              volume=False, grid=True)
        except Exception as e:
            logger.warning(f"绘图失败: {str(e)}")
        
    except Exception as e:
        logger.error(f"回测过程中出错: {str(e)}")
        logger.error("详细错误信息:", exc_info=True)

if __name__ == "__main__":
    run_backtest() 