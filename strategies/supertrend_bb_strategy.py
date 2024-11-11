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
        
        # 计算基准价格
        self.hl2 = (self.data.high + self.data.low) / 2
        
        # 计算上下轨
        self.up_band = self.hl2 + (self.p.atr_factor * self.atr)
        self.down_band = self.hl2 - (self.p.atr_factor * self.atr)
        
        # 使用Highest和Lowest代替HighestN和LowestN
        self.upperband = bt.indicators.Highest(
            self.up_band,
            period=1
        )
        self.lowerband = bt.indicators.Lowest(
            self.down_band,
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
        if len(self) < self.p.bb_period:  # 确保有足够的数据计算指标
            return
            
        if self.order:
            return
            
        # 入场条件
        if not self.position:
            # 多头入场：价格突破布林带下轨且ATR显示趋势向上
            if (self.data.close[0] < self.bb.lines.bot[0] and 
                self.data.close[0] > self.data.close[-1] and
                self.atr[0] > self.atr[-1]):
                size = self.calculate_size()
                self.log(f'多头信号: 价格 {self.data.close[0]:.2f} < 布林下轨 {self.bb.lines.bot[0]:.2f}')
                self.order = self.buy(size=size)
                
            # 空头入场：价格突破布林带上轨且ATR显示趋势向下
            elif (self.data.close[0] > self.bb.lines.top[0] and 
                  self.data.close[0] < self.data.close[-1] and
                  self.atr[0] > self.atr[-1]):
                size = self.calculate_size()
                self.log(f'空头信号: 价格 {self.data.close[0]:.2f} > 布林上轨 {self.bb.lines.top[0]:.2f}')
                self.order = self.sell(size=size)
                
        # 持有多头
        elif self.position.size > 0:
            # 当价格跌破中轨时平仓
            if self.data.close[0] < self.bb.lines.mid[0]:
                self.log(f'多头平仓: 价格 {self.data.close[0]:.2f} < 中轨 {self.bb.lines.mid[0]:.2f}')
                self.order = self.close()
                
        # 持有空头
        else:
            # 当价格突破中轨时平仓
            if self.data.close[0] > self.bb.lines.mid[0]:
                self.log(f'空头平仓: 价格 {self.data.close[0]:.2f} > 中轨 {self.bb.lines.mid[0]:.2f}')
                self.order = self.close()
                
    def calculate_size(self):
        """计算头寸大小"""
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        
        # 计算每笔交易的风险金额
        risk_amount = value * self.p.risk_ratio
        
        # 使用ATR计算止损点位
        stop_loss = self.atr[0] * 2
        
        # 如果止损为0，使用价格的1%作为止损
        if stop_loss == 0:
            stop_loss = self.data.close[0] * 0.01
            
        # 计算头寸大小
        size = risk_amount / stop_loss
        
        return size