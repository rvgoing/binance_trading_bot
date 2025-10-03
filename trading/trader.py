# trading/trader.py
"""
Trader class to manage trading loop and Binance API interaction
"""
import time
import logging
from binance.enums import *
from binance.exceptions import BinanceAPIException

class Trader:
    def __init__(self, client, strategy, symbol, quantity, interval, status_dict):
        self.client = client
        self.strategy = strategy
        self.symbol = symbol
        self.quantity = quantity
        self.interval = interval
        self.status = status_dict
        self.position = None
        self.entry_price = 0.0
        self.pnl = 0.0

    def get_klines(self, limit):
        try:
            klines = self.client.get_klines(symbol=self.symbol, interval=self.interval, limit=limit)
            closes = [float(k[4]) for k in klines]
            return closes
        except Exception as e:
            logging.error(f"Error fetching klines: {e}")
            return []

    def run(self, trading_active_flag, short_window, long_window):
        logging.info("Trading loop started.")
        while trading_active_flag():
            try:
                closes = self.get_klines(long_window + 1)
                if len(closes) < long_window:
                    time.sleep(10)
                    continue
                if self.strategy.should_buy(closes) and not self.position:
                    # BUY
                    self.client.create_test_order(
                        symbol=self.symbol,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_MARKET,
                        quantity=self.quantity
                    )
                    self.position = 'LONG'
                    self.entry_price = closes[-1]
                    logging.info(f"BUY {self.symbol} at {self.entry_price}")
                elif self.strategy.should_sell(closes) and self.position == 'LONG':
                    # SELL
                    self.client.create_test_order(
                        symbol=self.symbol,
                        side=SIDE_SELL,
                        type=ORDER_TYPE_MARKET,
                        quantity=self.quantity
                    )
                    pnl = (closes[-1] - self.entry_price) * self.quantity
                    self.pnl += pnl
                    logging.info(f"SELL {self.symbol} at {closes[-1]} | PnL: {self.pnl:.2f}")
                    self.position = None
                    self.entry_price = 0.0
                self.status['positions'] = [self.position] if self.position else []
                self.status['pnl'] = self.pnl
            except BinanceAPIException as e:
                logging.error(f"Binance API error: {e}")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            time.sleep(30)
        logging.info("Trading loop stopped.")
