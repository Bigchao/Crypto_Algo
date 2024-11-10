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

from strategies.turtle_trading import TurtleStrategy

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_turtle_strategy():
    """运行海龟交易策略回测"""
    try:
        # 创建cerebro引擎
        cerebro = bt.Cerebro()
        
        # 加载数据
        data_folder = os.path.join(project_root, 'kline_data')
        filename = 'BTCUSDT_4h_klines.h5'
        filepath = os.path.join(data_folder, filename)
        
        # 读取HDF5数据
        df = pd.read_hdf(filepath, key='klines')
        df.set_index('timestamp', inplace=True)
        
        # 创建数据源
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 使用索引作为时间戳
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1  # 不使用未平仓量
        )
        
        # 添加数据到回测引擎
        cerebro.adddata(data)
        
        # 设置初始资金
        cerebro.broker.setcash(100000.0)
        
        # 设置手续费
        cerebro.broker.setcommission(commission=0.001)
        
        # 添加策略
        cerebro.addstrategy(TurtleStrategy)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 打印初始资金
        logger.info('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 打印最终资金
        logger.info('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
        
        # 打印分析结果
        logger.info('\n=== 策略表现分析 ===')
        logger.info('夏普比率: %.2f' % strat.analyzers.sharpe.get_analysis()['sharperatio'])
        logger.info('最大回撤: %.2f%%' % strat.analyzers.drawdown.get_analysis()['max']['drawdown'])
        logger.info('年化收益率: %.2f%%' % strat.analyzers.returns.get_analysis()['rnorm100'])
        
        # 交易统计
        trade_analysis = strat.analyzers.trades.get_analysis()
        logger.info('\n=== 交易统计 ===')
        logger.info('总交易次数: %d' % trade_analysis['total']['total'])
        if trade_analysis['total']['total'] > 0:
            logger.info('盈利交易次数: %d' % trade_analysis['won']['total'])
            logger.info('亏损交易次数: %d' % trade_analysis['lost']['total'])
            logger.info('胜率: %.2f%%' % (trade_analysis['won']['total'] / trade_analysis['total']['total'] * 100))
            if trade_analysis['won']['total'] > 0:
                logger.info('平均盈利: %.2f' % trade_analysis['won']['pnl']['average'])
            if trade_analysis['lost']['total'] > 0:
                logger.info('平均亏损: %.2f' % trade_analysis['lost']['pnl']['average'])
        
        # 绘制图表
        cerebro.plot()
        
    except Exception as e:
        logger.error(f"回测过程中出错: {str(e)}")
        logger.error("详细错误信息:", exc_info=True)

if __name__ == "__main__":
    run_turtle_strategy() 