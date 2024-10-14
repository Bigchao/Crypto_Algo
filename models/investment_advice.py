def get_investment_advice(ahr999_value):
    if ahr999_value < 0.45:
        return "AHR999 index is below 0.45, it might be a good time to buy."
    elif 0.45 <= ahr999_value <= 1.2:
        return "AHR999 index is between 0.45 and 1.2, consider dollar-cost averaging."
    else:
        return "AHR999 index is above 1.2, the price is relatively high. Be cautious."
