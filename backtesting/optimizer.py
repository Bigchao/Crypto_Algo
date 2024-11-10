import backtrader as bt
import pandas as pd
import logging
import os
from strategies.turtle_trading import TurtleStrategy

logger = logging.getLogger(__name__)

class TurtleOptimizer:
    def __init__(self):
        self.cerebro = bt.Cerebro(optreturn=False)
        self.results = None
        
    def optimize_parameters(self, data_path, initial_cash=100000.0):
        """运行参数优化"""
        try:
            # 加载数据
            df = pd.read_hdf(data_path, key='klines')
            df.set_index('timestamp', inplace=True)
            data = bt.feeds.PandasData(dataname=df)
            self.cerebro.adddata(data)
            
            # 设置初始资金和手续费
            self.cerebro.broker.setcash(initial_cash)
            self.cerebro.broker.setcommission(commission=0.001)
            
            # 添加优化参数范围
            self.cerebro.optstrategy(
                TurtleStrategy,
                # 系统1参数
                sys1_entry_period=range(15, 26, 5),
                sys1_exit_period=range(8, 13, 2),
                # 系统2参数
                sys2_entry_period=range(50, 61, 5),
                sys2_exit_period=range(15, 26, 5),
                # 其他参数
                atr_period=range(15, 26, 5),
                risk_ratio=[0.01, 0.02, 0.03],
                units=range(3, 6),
                unit_gap=[0.3, 0.5, 0.7],
                sys1_allocation=[0.4, 0.5, 0.6],
                sys2_allocation=[0.4, 0.5, 0.6]
            )
            
            # 添加分析器
            self.add_analyzers()
            
            # 运行优化
            self.results = self.cerebro.run()
            
            # 分析结果
            self.analyze_results()
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            logger.error("Full error details:", exc_info=True) 