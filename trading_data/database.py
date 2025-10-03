import os
import sqlite3
import psycopg2
from datetime import datetime
import json
import hashlib

class TradingDatabase:
    def __init__(self):
        # 自動偵測使用哪種資料庫
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # PostgreSQL (Render/生產環境)
            self.db_type = 'postgres'
            self.conn = psycopg2.connect(database_url)
        else:
            # SQLite (本地開發)
            self.db_type = 'sqlite'
            os.makedirs('data', exist_ok=True)
            self.conn = sqlite3.connect('data/trading.db', check_same_thread=False)
            self.conn.execute('PRAGMA journal_mode=WAL')
        
        self.init_tables()
    
    def init_tables(self):
        if self.db_type == 'postgres':
            # PostgreSQL 語法
            self.conn.cursor().execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    trade_id VARCHAR(100) UNIQUE NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(20, 8) NOT NULL,
                    quantity DECIMAL(20, 8) NOT NULL,
                    pnl DECIMAL(20, 8),
                    balance DECIMAL(20, 8),
                    sma_short DECIMAL(20, 8),
                    sma_long DECIMAL(20, 8),
                    order_id VARCHAR(100)
                )
            ''')
            
            self.conn.cursor().execute('''
                CREATE TABLE IF NOT EXISTS system_state (
                    id INTEGER PRIMARY KEY,
                    position VARCHAR(10),
                    entry_price DECIMAL(20, 8),
                    balance DECIMAL(20, 8),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # SQLite 語法
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    pnl REAL,
                    balance REAL,
                    sma_short REAL,
                    sma_long REAL,
                    order_id TEXT
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS system_state (
                    id INTEGER PRIMARY KEY,
                    position TEXT,
                    entry_price REAL,
                    balance REAL,
                    updated_at TEXT
                )
            ''')
        
        self.conn.commit()
    
    def insert_trade(self, trade_data):
        """原子性插入交易記錄"""
        trade_id = f"{trade_data['symbol']}_{int(datetime.now().timestamp() * 1000)}"
        
        if self.db_type == 'postgres':
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO trades 
                (trade_id, timestamp, action, symbol, price, quantity, pnl, balance, sma_short, sma_long, order_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                trade_id,
                datetime.now(),
                trade_data['action'],
                trade_data['symbol'],
                trade_data['price'],
                trade_data['quantity'],
                trade_data.get('pnl'),
                trade_data.get('balance'),
                trade_data.get('sma_short'),
                trade_data.get('sma_long'),
                trade_data.get('order_id')
            ))
        else:
            self.conn.execute('''
                INSERT INTO trades 
                (trade_id, timestamp, action, symbol, price, quantity, pnl, balance, sma_short, sma_long, order_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_id,
                datetime.now().isoformat(),
                trade_data['action'],
                trade_data['symbol'],
                trade_data['price'],
                trade_data['quantity'],
                trade_data.get('pnl'),
                trade_data.get('balance'),
                trade_data.get('sma_short'),
                trade_data.get('sma_long'),
                trade_data.get('order_id')
            ))
        
        self.conn.commit()
        return trade_id
    
    def save_state(self, position, entry_price, balance):
        """儲存系統狀態"""
        if self.db_type == 'postgres':
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO system_state (id, position, entry_price, balance, updated_at)
                VALUES (1, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE 
                SET position = %s, entry_price = %s, balance = %s, updated_at = NOW()
            ''', (position, entry_price, balance, position, entry_price, balance))
        else:
            self.conn.execute('''
                INSERT OR REPLACE INTO system_state (id, position, entry_price, balance, updated_at)
                VALUES (1, ?, ?, ?, ?)
            ''', (position, entry_price, balance, datetime.now().isoformat()))
        
        self.conn.commit()
    
    def restore_state(self):
        """恢復系統狀態"""
        if self.db_type == 'postgres':
            cursor = self.conn.cursor()
            cursor.execute('SELECT position, entry_price, balance FROM system_state WHERE id=1')
            result = cursor.fetchone()
        else:
            cursor = self.conn.execute('SELECT position, entry_price, balance FROM system_state WHERE id=1')
            result = cursor.fetchone()
        
        if result:
            return {
                'position': result[0],
                'entry_price': float(result[1]) if result[1] else 0.0,
                'balance': float(result[2]) if result[2] else 1000.0
            }
        return None
    
    def get_statistics(self):
        """獲取交易統計"""
        if self.db_type == 'postgres':
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL' AND pnl > 0")
            wins = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(pnl) FROM trades WHERE action='SELL'")
            total_pnl = cursor.fetchone()[0] or 0
        else:
            cursor = self.conn.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
            total = cursor.fetchone()[0]
            
            cursor = self.conn.execute("SELECT COUNT(*) FROM trades WHERE action='SELL' AND pnl > 0")
            wins = cursor.fetchone()[0]
            
            cursor = self.conn.execute("SELECT SUM(pnl) FROM trades WHERE action='SELL'")
            total_pnl = cursor.fetchone()[0] or 0
        
        return {
            'total_trades': total,
            'winning_trades': wins,
            'win_rate': round((wins / total * 100) if total > 0 else 0, 2),
            'total_pnl': round(float(total_pnl), 4)
        }