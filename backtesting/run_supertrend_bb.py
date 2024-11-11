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

from strategies.supertrend_bb_strategy import SupertrendBBStrategy

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_backtest():
    """运行 Supertrend & Bollinger Bands 策略回测"""
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
        cerebro.addstrategy(SupertrendBBStrategy)
        
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
        final_value = cerebro.broker.getvalue()
        initial_value = 100000.0
        total_return = (final_value - initial_value) / initial_value * 100
        
        logger.info('Final Portfolio Value: %.2f' % final_value)
        logger.info(f'Total Return: {total_return:.2f}%')
        
        # 打印分析结果
        logger.info('\n=== 策略表现分析 ===')
        
        # 夏普比率
        sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0.0)
        logger.info('夏普比率: %.2f' % (sharpe_ratio if sharpe_ratio is not None else 0.0))
        
        # 最大回撤
        drawdown = strat.analyzers.drawdown.get_analysis()
        max_drawdown = drawdown.get('max', {}).get('drawdown', 0.0)
        logger.info('最大回撤: %.2f%%' % (max_drawdown if max_drawdown is not None else 0.0))
        
        # 年化收益率
        returns = strat.analyzers.returns.get_analysis()
        annual_return = returns.get('rnorm100', 0.0)
        logger.info('年化收益率: %.2f%%' % (annual_return if annual_return is not None else 0.0))
        
        # 交易统计
        trade_analysis = strat.analyzers.trades.get_analysis()
        logger.info('\n=== 交易统计 ===')
        total_trades = trade_analysis.get('total', {}).get('total', 0)
        logger.info('总交易次数: %d' % total_trades)
        
        if total_trades > 0:
            won_trades = trade_analysis.get('won', {}).get('total', 0)
            lost_trades = trade_analysis.get('lost', {}).get('total', 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            logger.info('盈利交易次数: %d' % won_trades)
            logger.info('亏损交易次数: %d' % lost_trades)
            logger.info('胜率: %.2f%%' % win_rate)
            
            # 平均盈亏
            avg_won = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0.0)
            avg_lost = trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0.0)
            
            if won_trades > 0:
                logger.info('平均盈利: %.2f' % avg_won)
            if lost_trades > 0:
                logger.info('平均亏损: %.2f' % avg_lost)
                
            # 盈亏比
            if avg_lost != 0:
                profit_factor = abs(avg_won/avg_lost) if avg_lost != 0 else 0
                logger.info('盈亏比: %.2f' % profit_factor)
        
        # 绘制图表
        cerebro.plot()
        
    except Exception as e:
        logger.error(f"回测过程中出错: {str(e)}")
        logger.error("详细错误信息:", exc_info=True)

if __name__ == "__main__":
    run_backtest() 