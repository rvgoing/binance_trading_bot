# trading/utils.py
"""
Utility functions for the trading bot
"""
import logging
import time

def retry_on_exception(func, retries=3, delay=5, exceptions=(Exception,)):
    """
    Retry a function call with specified retries and delay on given exceptions.
    """
    for attempt in range(retries):
        try:
            return func()
        except exceptions as e:
            logging.warning(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

def format_pnl(pnl):
    """
    Format profit and loss as a string with 2 decimals and sign.
    """
    return f"{pnl:+.2f}"
