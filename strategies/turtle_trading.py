import logging
import backtrader as bt

logger = logging.getLogger(__name__)

class TurtleStrategy(bt.Strategy):
    """海龟交易策略实现 (系统1+系统2)"""
    
    params = (
        # 系统1参数
        ('sys1_entry_period', 20),    # 系统1入场周期
        ('sys1_exit_period', 10),     # 系统1退出周期
        # 系统2参数
        ('sys2_entry_period', 55),    # 系统2入场周期
        ('sys2_exit_period', 20),     # 系统2退出周期
        # 共同参数
        ('atr_period', 20),           # ATR周期
        ('risk_ratio', 0.02),         # 账户风险比例
        ('units', 4),                 # 最大加仓次数
        ('unit_gap', 0.5),            # 加仓间隔（0.5N）
        ('sys1_allocation', 0.5),     # 系统1资金分配比例
        ('sys2_allocation', 0.5),     # 系统2资金分配比例
    )
    
    def __init__(self):
        """初始化策略"""
        super(TurtleStrategy, self).__init__()
        
        # ATR和系统1的唐奇安通道
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        self.sys1_entry_high = bt.indicators.Highest(self.data.high, period=self.p.sys1_entry_period)
        self.sys1_entry_low = bt.indicators.Lowest(self.data.low, period=self.p.sys1_entry_period)
        self.sys1_exit_high = bt.indicators.Highest(self.data.high, period=self.p.sys1_exit_period)
        self.sys1_exit_low = bt.indicators.Lowest(self.data.low, period=self.p.sys1_exit_period)
        
        # 系统2的唐奇安通道
        self.sys2_entry_high = bt.indicators.Highest(self.data.high, period=self.p.sys2_entry_period)
        self.sys2_entry_low = bt.indicators.Lowest(self.data.low, period=self.p.sys2_entry_period)
        self.sys2_exit_high = bt.indicators.Highest(self.data.high, period=self.p.sys2_exit_period)
        self.sys2_exit_low = bt.indicators.Lowest(self.data.low, period=self.p.sys2_exit_period)
        
        # 交易状态
        self.sys1_order = None
        self.sys2_order = None
        self.sys1_units_long = 0
        self.sys1_units_short = 0
        self.sys2_units_long = 0
        self.sys2_units_short = 0
        self.sys1_entry_price_long = 0
        self.sys1_entry_price_short = 0
        self.sys2_entry_price_long = 0
        self.sys2_entry_price_short = 0
        
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
        
    def calculate_unit_size(self):
        """计算单位头寸大小"""
        return (self.broker.getvalue() * self.p.risk_ratio) / self.atr[0]
        
    def print_strategy_info(self):
        """打印策略基本信息"""
        logger.info("\n" + "="*50)
        logger.info("海龟交易策略状态报告")
        logger.info("="*50)
        
        # 账户信息
        portfolio_value = self.broker.getvalue()
        cash = self.broker.getcash()
        logger.info(f"\n账户信息:")
        logger.info(f"总资产: {portfolio_value:,.2f} USDT")
        logger.info(f"可用资金: {cash:,.2f} USDT")
        
        # 当前持仓
        logger.info(f"\n当前持仓:")
        if self.position:
            logger.info(f"持仓大小: {self.position.size}")
            logger.info(f"持仓成本: {self.position.price:.2f}")
            logger.info(f"当前市值: {self.position.size * self.data.close[0]:.2f}")
            logger.info(f"未实现盈亏: {(self.data.close[0] - self.position.price) * self.position.size:.2f}")
        else:
            logger.info("当前无持仓")
        
        # 系统1状态
        logger.info(f"\n系统1状态:")
        logger.info(f"多头单位数: {self.sys1_units_long}")
        logger.info(f"空头单位数: {self.sys1_units_short}")
        if self.sys1_entry_price_long:
            logger.info(f"多头入场价: {self.sys1_entry_price_long:.2f}")
        if self.sys1_entry_price_short:
            logger.info(f"空头入场价: {self.sys1_entry_price_short:.2f}")
        
        # 系统2状态
        logger.info(f"\n系统2状态:")
        logger.info(f"多头单位数: {self.sys2_units_long}")
        logger.info(f"空头单位数: {self.sys2_units_short}")
        if self.sys2_entry_price_long:
            logger.info(f"多头入场价: {self.sys2_entry_price_long:.2f}")
        if self.sys2_entry_price_short:
            logger.info(f"空头入场价: {self.sys2_entry_price_short:.2f}")
        
        # 技术指标
        logger.info(f"\n技术指标:")
        logger.info(f"当前ATR: {self.atr[0]:.2f}")
        logger.info(f"系统1入场通道上轨: {self.sys1_entry_high[0]:.2f}")
        logger.info(f"系统1入场通道下轨: {self.sys1_entry_low[0]:.2f}")
        logger.info(f"系统2入场通道上轨: {self.sys2_entry_high[0]:.2f}")
        logger.info(f"系统2入场通道下轨: {self.sys2_entry_low[0]:.2f}")
        
        logger.info("\n" + "="*50)

    def next(self):
        """主要策略逻辑"""
        # 每100个周期打印一次策略信息
        if len(self) % 100 == 0:
            self.print_strategy_info()
        
        # 首先检查止损
        self.check_stop_loss()
        
        # 然后检查系统1和系统2的信号
        self.check_sys1_signals()
        self.check_sys2_signals()
        
    def check_sys1_signals(self):
        if self.sys1_order:
            return
            
        # 没有持仓 - 寻找入场机会
        if not self.position:
            # 多头入场
            if self.data.close[0] > self.sys1_entry_high[-1]:
                size = self.calculate_unit_size()
                self.sys1_order = self.buy(size=size)
                self.sys1_entry_price_long = self.data.close[0]
                self.sys1_units_long = 1
                self.log(f'BUY CREATE {size:.2f} @ Price {self.data.close[0]:.2f}')
                
            # 空头入场
            elif self.data.close[0] < self.sys1_entry_low[-1]:
                size = self.calculate_unit_size()
                self.sys1_order = self.sell(size=size)
                self.sys1_entry_price_short = self.data.close[0]
                self.sys1_units_short = 1
                self.log(f'SELL CREATE {size:.2f} @ Price {self.data.close[0]:.2f}')
                
        # 持有多头
        elif self.position.size > 0:
            # 加仓
            if (self.data.close[0] >= self.sys1_entry_price_long + self.atr[0] * self.p.unit_gap and 
                self.sys1_units_long < self.p.units):
                size = self.calculate_unit_size()
                self.sys1_order = self.buy(size=size)
                self.sys1_entry_price_long = self.data.close[0]
                self.sys1_units_long += 1
                self.log(f'BUY ADD {size:.2f} @ Price {self.data.close[0]:.2f}')
                
            # 退出
            elif self.data.close[0] < self.sys1_exit_low[-1]:
                self.sys1_order = self.close()
                self.sys1_units_long = 0
                self.log(f'LONG EXIT @ Price {self.data.close[0]:.2f}')
                
        # 持有空头
        else:
            # 加仓
            if (self.data.close[0] <= self.sys1_entry_price_short - self.atr[0] * self.p.unit_gap and 
                self.sys1_units_short < self.p.units):
                size = self.calculate_unit_size()
                self.sys1_order = self.sell(size=size)
                self.sys1_entry_price_short = self.data.close[0]
                self.sys1_units_short += 1
                self.log(f'SELL ADD {size:.2f} @ Price {self.data.close[0]:.2f}')
                
            # 退出
            elif self.data.close[0] > self.sys1_exit_high[-1]:
                self.sys1_order = self.close()
                self.sys1_units_short = 0
                self.log(f'SHORT EXIT @ Price {self.data.close[0]:.2f}')
                
    def check_sys2_signals(self):
        if self.sys2_order:
            return
            
        # 没有持仓 - 寻找入场机会
        if not self.position:
            # 多头入场
            if self.data.close[0] > self.sys2_entry_high[-1]:
                size = self.calculate_unit_size()
                self.sys2_order = self.buy(size=size)
                self.sys2_entry_price_long = self.data.close[0]
                self.sys2_units_long = 1
                self.log(f'BUY CREATE {size:.2f} @ Price {self.data.close[0]:.2f}')
                
            # 空头入场
            elif self.data.close[0] < self.sys2_entry_low[-1]:
                size = self.calculate_unit_size()
                self.sys2_order = self.sell(size=size)
                self.sys2_entry_price_short = self.data.close[0]
                self.sys2_units_short = 1
                self.log(f'SELL CREATE {size:.2f} @ Price {self.data.close[0]:.2f}')
                
        # 持有多头
        elif self.position.size > 0:
            # 加仓
            if (self.data.close[0] >= self.sys2_entry_price_long + self.atr[0] * self.p.unit_gap and 
                self.sys2_units_long < self.p.units):
                size = self.calculate_unit_size()
                self.sys2_order = self.buy(size=size)
                self.sys2_entry_price_long = self.data.close[0]
                self.sys2_units_long += 1
                self.log(f'BUY ADD {size:.2f} @ Price {self.data.close[0]:.2f}')
                
            # 退出
            elif self.data.close[0] < self.sys2_exit_low[-1]:
                self.sys2_order = self.close()
                self.sys2_units_long = 0
                self.log(f'LONG EXIT @ Price {self.data.close[0]:.2f}')
                
        # 持有空头
        else:
            # 加仓
            if (self.data.close[0] <= self.sys2_entry_price_short - self.atr[0] * self.p.unit_gap and 
                self.sys2_units_short < self.p.units):
                size = self.calculate_unit_size()
                self.sys2_order = self.sell(size=size)
                self.sys2_entry_price_short = self.data.close[0]
                self.sys2_units_short += 1
                self.log(f'SELL ADD {size:.2f} @ Price {self.data.close[0]:.2f}')
                
            # 退出
            elif self.data.close[0] > self.sys2_exit_high[-1]:
                self.sys2_order = self.close()
                self.sys2_units_short = 0
                self.log(f'SHORT EXIT @ Price {self.data.close[0]:.2f}')
                
    def notify_order(self, order):
        """订单状态更新通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.sys1_order = None
        self.sys2_order = None

    def check_stop_loss(self):
        """检查止损条件"""
        # 系统1的止损
        if self.sys1_units_long > 0:
            stop_price = self.sys1_entry_price_long - 2 * self.atr[0]
            if self.data.close[0] < stop_price:
                self.close()
                self.sys1_units_long = 0
                self.log(f'SYS1 STOP LOSS @ Price {self.data.close[0]:.2f}')
                
        elif self.sys1_units_short > 0:
            stop_price = self.sys1_entry_price_short + 2 * self.atr[0]
            if self.data.close[0] > stop_price:
                self.close()
                self.sys1_units_short = 0
                self.log(f'SYS1 STOP LOSS @ Price {self.data.close[0]:.2f}')
                
        # 系统2的止损
        if self.sys2_units_long > 0:
            stop_price = self.sys2_entry_price_long - 2 * self.atr[0]
            if self.data.close[0] < stop_price:
                self.close()
                self.sys2_units_long = 0
                self.log(f'SYS2 STOP LOSS @ Price {self.data.close[0]:.2f}')
                
        elif self.sys2_units_short > 0:
            stop_price = self.sys2_entry_price_short + 2 * self.atr[0]
            if self.data.close[0] > stop_price:
                self.close()
                self.sys2_units_short = 0
                self.log(f'SYS2 STOP LOSS @ Price {self.data.close[0]:.2f}')

    def allocate_capital(self, system_type):
        """计算每个系统可用的资金"""
        total_equity = self.broker.getvalue()
        if system_type == 'sys1':
            return total_equity * self.p.sys1_allocation
        else:
            return total_equity * self.p.sys2_allocation

    def calculate_position_size(self, system_type):
        """计算头寸规模"""
        # 获取系统可用资金
        available_capital = self.allocate_capital(system_type)
        
        # 计算每N的美元价值
        dollar_volatility = self.atr[0]
        
        # 计算单位头寸规模
        position_size = (available_capital * self.p.risk_ratio) / dollar_volatility
        
        # 考虑最小交易单位
        min_trade_unit = 0.001  # BTC最小交易单位
        position_size = round(position_size / min_trade_unit) * min_trade_unit
        
        return position_size

    def print_final_stats(self):
        """打印最终的策略性能统计"""
        logger.info("\n" + "="*50)
        logger.info("海龟交易策略最终表现")
        logger.info("="*50)
        
        # 计算收益率
        initial_value = self.broker.startingcash
        final_value = self.broker.getvalue()
        total_return = (final_value - initial_value) / initial_value * 100
        
        # 计算年化收益率
        days = len(self.data)
        annual_return = (1 + total_return/100) ** (365/days) - 1
        
        # 计算最大回撤
        max_drawdown = 0
        peak = self.broker.startingcash
        for i in range(len(self.data)):
            value = self.broker.get_value([self.data.datetime[i]])
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 输出性能指标
        logger.info(f"\n收益统计:")
        logger.info(f"初始资金: {initial_value:,.2f} USDT")
        logger.info(f"最终资金: {final_value:,.2f} USDT")
        logger.info(f"总收益率: {total_return:.2f}%")
        logger.info(f"年化收益率: {annual_return*100:.2f}%")
        logger.info(f"最大回撤: {max_drawdown:.2f}%")
        
        # 交易统计
        logger.info(f"\n交易统计:")
        logger.info(f"总交易次数: {self.total_trades}")
        if self.total_trades > 0:
            logger.info(f"胜率: {(self.winning_trades/self.total_trades)*100:.2f}%")
            logger.info(f"平均盈利: {self.total_profit/self.winning_trades if self.winning_trades > 0 else 0:.2f} USDT")
            logger.info(f"平均亏损: {self.total_loss/self.losing_trades if self.losing_trades > 0 else 0:.2f} USDT")
            logger.info(f"盈亏比: {abs(self.total_profit/self.winning_trades)/(abs(self.total_loss/self.losing_trades)) if self.losing_trades > 0 else 'N/A':.2f}")
        
        logger.info("\n" + "="*50)
