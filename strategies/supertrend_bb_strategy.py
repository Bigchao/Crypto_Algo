import backtrader as bt
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SupertrendBBStrategy(bt.Strategy):
    """
    结合Supertrend和布林带的交易策略
    """
    params = (
        ('atr_period', 10),           # ATR周期
        ('atr_factor', 3),            # Supertrend因子
        ('bb_period', 20),            # 布林带周期
        ('bb_deviation', 2),          # 布林带标准差倍数
        ('risk_ratio', 0.02),         # 账户风险比例
    )
    
    def __init__(self):
        super(SupertrendBBStrategy, self).__init__()
        
        # 计算ATR
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        
        # 计算布林带
        self.bb = bt.indicators.BollingerBands(
            period=self.p.bb_period,
            devfactor=self.p.bb_deviation
        )
        
        # 计算Supertrend
        self.tr = bt.indicators.TrueRange()
        self.atr = bt.indicators.SmoothedMovingAverage(
            self.tr,
            period=self.p.atr_period
        )
        
        # 计算上下轨
        self.upperband = bt.indicators.HighestN(
            (self.data.high + self.data.low) / 2 + 
            self.p.atr_factor * self.atr,
            period=1
        )
        self.lowerband = bt.indicators.LowestN(
            (self.data.high + self.data.low) / 2 - 
            self.p.atr_factor * self.atr,
            period=1
        )
        
        # 交易状态
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 趋势方向
        self.trend = 0  # 1: 上涨, -1: 下跌
        
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
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, '
                        f'Comm: {order.executed.comm:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.order = None
        
    def next(self):
        """主要策略逻辑"""
        if self.order:
            return
            
        # 更新趋势方向
        if self.data.close[0] > self.upperband[0]:
            self.trend = 1
        elif self.data.close[0] < self.lowerband[0]:
            self.trend = -1
            
        # 入场条件
        if not self.position:
            # 多头入场：价格突破Supertrend上轨且低于布林带下轨
            if (self.data.close[0] > self.upperband[0] and 
                self.data.close[0] < self.bb.lines.bot[0]):
                size = self.calculate_size()
                self.log(f'BUY CREATE {size:.2f} @ Price {self.data.close[0]:.2f}')
                self.order = self.buy(size=size)
                
            # 空头入场：价格突破Supertrend下轨且高于布林带上轨
            elif (self.data.close[0] < self.lowerband[0] and 
                  self.data.close[0] > self.bb.lines.top[0]):
                size = self.calculate_size()
                self.log(f'SELL CREATE {size:.2f} @ Price {self.data.close[0]:.2f}')
                self.order = self.sell(size=size)
                
        # 持有多头
        elif self.position.size > 0:
            # 当价格跌破Supertrend下轨时平仓
            if self.data.close[0] < self.lowerband[0]:
                self.log(f'CLOSE LONG @ Price {self.data.close[0]:.2f}')
                self.order = self.close()
                
        # 持有空头
        else:
            # 当价格突破Supertrend上轨时平仓
            if self.data.close[0] > self.upperband[0]:
                self.log(f'CLOSE SHORT @ Price {self.data.close[0]:.2f}')
                self.order = self.close()
                
    def calculate_size(self):
        """计算头寸规模"""
        value = self.broker.getvalue()
        price = self.data.close[0]
        size = (value * self.p.risk_ratio) / price
        return size 