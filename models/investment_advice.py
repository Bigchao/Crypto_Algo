def get_investment_advice(ahr999_value):
    if ahr999_value < 0.45:
        return "AHR999指数低于0.45，现在是抄底的好时机。"
    elif 0.45 <= ahr999_value <= 1.2:
        return "AHR999指数在0.45到1.2之间，适合定投。"
    else:
        return "AHR999指数高于1.2，币价较高，建议谨慎操作。"
