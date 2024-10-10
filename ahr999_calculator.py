from models.price_prediction import calculate_ahr999, get_current_price
from datetime import datetime

def get_ahr999():
    """
    计算并返回当前的AHR999指数值和BTC价格。
    
    返回:
    tuple: (ahr999值, BTC价格, 时间戳)
    """
    try:
        ahr999, timestamp = calculate_ahr999()
        btc_price = get_current_price()  # 假设这个函数存在于 price_prediction.py 中
        return ahr999, btc_price, timestamp
    except Exception as e:
        print(f"计算AHR999时发生错误: {str(e)}")
        return None, None, datetime.now()

def format_ahr999_message(ahr999, btc_price, timestamp):
    """
    格式化AHR999指数和BTC价格消息。
    
    参数:
    ahr999 (float): AHR999指数值
    btc_price (float): BTC当前价格
    timestamp (datetime): 计算时间戳
    
    返回:
    str: 格式化的消息
    """
    if ahr999 is None or btc_price is None:
        return "抱歉，计算AHR999指数或获取BTC价格时出现错误。请稍后再试。"
    
    message = f"BTC当前价格: ${btc_price:,.2f}\n"
    message += f"AHR999指数: {ahr999:.4f}\n"
    
    if ahr999 < 0.45:
        message += "市场状态: 极度恐慌 (建议买入)\n"
    elif 0.45 <= ahr999 < 1.2:
        message += "市场状态: 中性（建议定投）\n"
    else:
        message += "市场状态: 极度贪婪 (建议卖出)\n"
    
    message += f"计算时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    return message

def get_ahr999_message():
    """
    获取格式化的AHR999指数和BTC价格消息。
    
    返回:
    str: 格式化的AHR999指数和BTC价格消息
    """
    ahr999, btc_price, timestamp = get_ahr999()
    return format_ahr999_message(ahr999, btc_price, timestamp)

if __name__ == "__main__":
    # 用于测试
    print(get_ahr999_message())
