from database import TradingDatabase
import sqlite3

db = TradingDatabase()

print("\n=== 交易統計 ===")
stats = db.get_statistics()
for key, value in stats.items():
    print(f"{key}: {value}")

print("\n=== 最近 10 筆交易 ===")
cursor = db.conn.execute('''
    SELECT timestamp, action, price, quantity, pnl 
    FROM trades 
    ORDER BY timestamp DESC 
    LIMIT 10
''')

for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]} | Price: {row[2]} | Qty: {row[3]} | PnL: {row[4]}")

print("\n=== 當前狀態 ===")
state = db.restore_state()
if state:
    print(f"Position: {state['position']}")
    print(f"Entry Price: {state['entry_price']}")
    print(f"Balance: {state['balance']}")
else:
    print("No saved state")