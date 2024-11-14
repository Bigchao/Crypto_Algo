import pandas as pd
import numpy as np
import logging
from datetime import datetime
import backtrader as bt

logger = logging.getLogger(__name__)

class SpotFuturesHedgeStrategy(bt.Strategy):
    """
    现货-合约对冲策略
    
    基本逻辑：
    1. 持有现货多头仓位
    2. 在合约端做空对冲风险
    3. 根据资金费率调整对冲比例
    """
    
    params = (
        ('hedge_ratio', 0.8),        # 对冲比例（0.8表示用80%的仓位做对冲）
        ('funding_threshold', 0.001), # 资金费率阈值
        ('position_size', 1.0),      # 基础仓位大小
        ('leverage', 3),             # 合约杠杆倍数
    )
    
    def __init__(self):
        super(SpotFuturesHedgeStrategy, self).__init__()
        
        # 加载现货和合约数据
        self.spot_data = self.datas[0]      # 现货数据
        self.futures_data = self.datas[1]   # 合约数据
        self.funding_data = self.datas[2]   # 资金费率数据
        
        # 初始化订单和持仓状态
        self.order = None            # 当前订单
        self.spot_position = None    # 现货仓位
        self.futures_position = None # 合约仓位
        
        # 记录当前对冲比例
        self.current_hedge_ratio = self.p.hedge_ratio
        
        # 记录交易状态
        self.spot_orders = []        # 现货订单列表
        self.futures_orders = []     # 合约订单列表
        self.trades = []             # 交易记录
        
    def next(self):
        """主要策略逻辑"""
        if self.order:  # 如果有未完成的订单，等待
            return
            
        # 获取当前价格和资金费率
        spot_price = self.spot_data.close[0]
        futures_price = self.futures_data.close[0]
        current_funding_rate = self.funding_data[0]
        
        # 计算现货和合约的价差
        basis = futures_price - spot_price
        basis_percent = basis / spot_price
        
        # 记录当前状态
        self.log(f'现货价格: {spot_price:.2f}, 合约价格: {futures_price:.2f}, '
                f'基差: {basis_percent:.4%}, 资金费率: {current_funding_rate:.4%}')
        
        # 根据资金费率调整对冲比例
        if abs(current_funding_rate) > self.p.funding_threshold:
            if current_funding_rate > 0:  # 多头付费
                # 减少合约空头仓位
                new_hedge_ratio = max(0.5, self.current_hedge_ratio - 0.1)
            else:  # 空头付费
                # 增加合约空头仓位
                new_hedge_ratio = min(1.0, self.current_hedge_ratio + 0.1)
                
            if new_hedge_ratio != self.current_hedge_ratio:
                self.adjust_hedge_ratio(new_hedge_ratio)
    
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
        
    def notify_order(self, order):
        """订单状态更新通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格 {order.executed.price:.2f}, '
                        f'数量 {order.executed.size:.3f}, '
                        f'成本 {order.executed.value:.2f}, '
                        f'手续费 {order.executed.comm:.2f}')
            else:
                self.log(f'卖出执行: 价格 {order.executed.price:.2f}, '
                        f'数量 {order.executed.size:.3f}, '
                        f'成本 {order.executed.value:.2f}, '
                        f'手续费 {order.executed.comm:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
            
        self.order = None