import os
import threading
import time
import logging
from flask import Flask, jsonify
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

# Load environment variables FROM .env directly
# Load environment variables
# load_dotenv()

# BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
# BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
# BINANCE_MODE = os.getenv('BINANCE_MODE', 'test')

# Load environment variables FROM .env directly
# Load evnvironment variables using SecureConfig

from secure_config import SecureConfig

sc = SecureConfig()
config = sc.load_decrypted_env()

BINANCE_API_KEY = config['BINANCE_API_KEY']
BINANCE_SECRET_KEY = config['BINANCE_SECRET_KEY']
BINANCE_MODE = config.get('BINANCE_MODE', 'test')

print("API MODE:", BINANCE_MODE)

# Logging setup
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)


# Binance endpoint selection
if BINANCE_MODE == 'test':
    BINANCE_API_URL = 'https://testnet.binance.vision'
else:
    BINANCE_API_URL = 'https://api.binance.com'

# ✅ 正確初始化 client
if BINANCE_MODE == 'test':
    client = Client(
        BINANCE_API_KEY, 
        BINANCE_SECRET_KEY,
        testnet=True
    )
    logging.info("🧪 Using Binance TESTNET - No real money involved")
else:
    client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
    logging.warning("⚠️  Using Binance LIVE - Real trading mode!")

#======================================


app = Flask(__name__)

# Root route
@app.route('/', methods=['GET'])
def index():
    return """
    <html>
        <head><title>Binance Quantitative Trading Bot API</title></head>
        <body style='font-family:sans-serif;'>
            <h1>Welcome to the Binance Quantitative Trading Bot API</h1>
            <p>Available endpoints:</p>
            <ul>
                <li><b>GET</b> <code>/health</code></li>
                <li><b>POST</b> <code>/trade</code> (start trading)</li>
                <li><b>GET</b> <code>/trade</code> (status)</li>
            </ul>
        </body>
    </html>
    """

# Trading state
trading_thread = None
trading_active = False
trading_status = {
    'active': False,
    'positions': [],
    'pnl': 0.0
}

# Sample trading strategy: SMA crossover
SYMBOL = 'BTCUSDT'
INTERVAL = Client.KLINE_INTERVAL_1MINUTE
QUANTITY = 0.001
SHORT_WINDOW = 5
LONG_WINDOW = 10


def get_klines(symbol, interval, limit=LONG_WINDOW+1, max_retries=3):
    for attempt in range(max_retries):
        try:
            klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            closes = [float(k[4]) for k in klines]
            return closes
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5
                logging.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logging.error(f"Failed after {max_retries} attempts: {e}")
                return []

def calculate_sma(data, window):
    if len(data) < window:
        return None
    return sum(data[-window:]) / window

def trading_loop():
    global trading_active, trading_status
    position = None
    entry_price = 0.0
    pnl = 0.0
    logging.info("Trading loop started.")
    while trading_active:
        try:
            closes = get_klines(SYMBOL, INTERVAL)
            if len(closes) < LONG_WINDOW:
                time.sleep(10)
                continue
            sma_short = calculate_sma(closes, SHORT_WINDOW)
            sma_long = calculate_sma(closes, LONG_WINDOW)
            price = closes[-1]
            # Simple SMA crossover logic
            if sma_short and sma_long:
                if sma_short > sma_long and not position:
                    # BUY
                    order = client.create_test_order(
                        symbol=SYMBOL,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_MARKET,
                        quantity=QUANTITY
                    )
                    position = 'LONG'
                    entry_price = price
                    logging.info(f"BUY {SYMBOL} at {price}")
                elif sma_short < sma_long and position == 'LONG':
                    # SELL
                    order = client.create_test_order(
                        symbol=SYMBOL,
                        side=SIDE_SELL,
                        type=ORDER_TYPE_MARKET,
                        quantity=QUANTITY
                    )
                    pnl += (price - entry_price) * QUANTITY
                    position = None
                    entry_price = 0.0
                    logging.info(f"SELL {SYMBOL} at {price} | PnL: {pnl:.2f}")
            trading_status['positions'] = [position] if position else []
            trading_status['pnl'] = pnl
        except BinanceAPIException as e:
            logging.error(f"Binance API error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        time.sleep(30)
    logging.info("Trading loop stopped.")

@app.route('/health', methods=['GET'])
def health():
    # Check Binance API connectivity
    try:
        server_time = client.get_server_time()
        binance_status = 'ok'
    except Exception as e:
        binance_status = f'error: {str(e)}'

    # Check API Key & Secret Key validity
    try:
        # This will fail if keys are invalid or have no permission
        account_info = client.get_account()
        key_status = 'ok'
    except Exception as e:
        key_status = f'error: {str(e)}'

    return jsonify({
        'status': 'OK',
        'binance_api': binance_status,
        'api_key_status': key_status
    })



from flask import request, abort, jsonify

# HTML control page for /trade
@app.route('/trade', methods=['GET'])
def trade_page():
    return f"""
    <html>
    <head>
        <title>Trading Control Panel</title>
        <style>
            body {{ font-family: sans-serif; }}
            button {{ margin: 0.5em; padding: 0.5em 1em; font-size: 1em; }}
            #result {{ margin-top: 1em; }}
        </style>
    </head>
    <body>
        <h1>Trading Control Panel</h1>
        <button onclick="startTrading()">Start Trading</button>
        <button onclick="getStatus()">Get Status</button>
        <button onclick="stopTrading()">Stop Trading</button>
        <div id="result"></div>
        <script>
        function startTrading() {{
            fetch('/api/trade/start', {{method: 'POST'}})
                .then(r => r.json()).then(d => showResult(d));
        }}
        function getStatus() {{
            fetch('/api/trade/status')
                .then(r => r.json()).then(d => showResult(d));
        }}
        function stopTrading() {{
            fetch('/api/trade/stop', {{method: 'POST'}})
                .then(r => r.json()).then(d => showResult(d));
        }}
        function showResult(d) {{
            let html = '<pre>' + JSON.stringify(d, null, 2) + '</pre>';
            document.getElementById('result').innerHTML = html;
        }}
        </script>
        <a href='/'>Back to Home</a>
    </body>
    </html>
    """

# RESTful API endpoints for trading control
@app.route('/api/trade/start', methods=['POST'])
def api_trade_start():
    global trading_thread, trading_active
    if trading_active:
        return jsonify({'status': 'error', 'message': 'Trading already running.'}), 400
    trading_active = True
    trading_thread = threading.Thread(target=trading_loop, daemon=True)
    trading_thread.start()
    return jsonify({'status': 'success', 'message': 'Trading started.'})

@app.route('/api/trade/status', methods=['GET'])
def api_trade_status():
    return jsonify({
        'active': trading_active,
        'positions': trading_status['positions'],
        'pnl': trading_status['pnl']
    })

@app.route('/api/trade/stop', methods=['POST'])
def api_trade_stop():
    global trading_active
    if not trading_active:
        return jsonify({'status': 'error', 'message': 'Trading is not running.'}), 400
    trading_active = False
    return jsonify({'status': 'success', 'message': 'Trading stopped.'})

def test_connection():
    try:
        # 測試伺服器時間
        server_time = client.get_server_time()
        logging.info(f"✅ Server time: {server_time}")
        
        # 測試獲取 K 線
        klines = client.get_klines(symbol='BTCUSDT', interval='1m', limit=5)
        logging.info(f"✅ Got {len(klines)} klines")
        
        return True
    except Exception as e:
        logging.error(f"❌ Connection test failed: {e}")
        return False

# 在啟動前測試
if __name__ == '__main__':
    if not test_connection():
        logging.error("無法連接幣安 API！")
        exit(1)
    else:
        logging.info("已經連接幣安 API！")
        print("\n已經連接幣安 API！\n")
    app.run(host='0.0.0.0', port=5000)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
