# trading/strategy.py
"""
Sample trading strategy logic (SMA crossover)
"""

def calculate_sma(data, window):
    if len(data) < window:
        return None
    return sum(data[-window:]) / window

class SMACrossoverStrategy:
    def __init__(self, short_window=5, long_window=10):
        self.short_window = short_window
        self.long_window = long_window

    def should_buy(self, closes):
        sma_short = calculate_sma(closes, self.short_window)
        sma_long = calculate_sma(closes, self.long_window)
        return sma_short and sma_long and sma_short > sma_long

    def should_sell(self, closes):
        sma_short = calculate_sma(closes, self.short_window)
        sma_long = calculate_sma(closes, self.long_window)
        return sma_short and sma_long and sma_short < sma_long
