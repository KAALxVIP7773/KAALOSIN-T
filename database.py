
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            credits REAL DEFAULT 0.0,
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE'
        )
        ''')
        
        # Transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Referral codes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_codes (
            code TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Services usage table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_type TEXT,
            query TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id, username=None, first_name=None, referred_by=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return False
        
        # Add new user with bonus credits
        bonus_credits = 5.0  # Welcome bonus
        cursor.execute('''
        INSERT INTO users (user_id, username, first_name, credits, referred_by)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, bonus_credits, referred_by))
        
        # Generate referral code
        ref_code = self.generate_referral_code(user_id)
        cursor.execute('''
        INSERT INTO referral_codes (code, user_id) VALUES (?, ?)
        ''', (ref_code, user_id))
        
        # Add transaction record
        cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, description)
        VALUES (?, ?, ?, ?)
        ''', (user_id, 'BONUS', bonus_credits, 'Welcome bonus'))
        
        # Update referrer's credits and referral count
        if referred_by:
            cursor.execute('''
            UPDATE users SET credits = credits + 1.0, referrals = referrals + 1
            WHERE user_id = ?
            ''', (referred_by,))
            
            cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (?, ?, ?, ?)
            ''', (referred_by, 'REFERRAL', 1.0, f'Referral bonus for user {user_id}'))
        
        conn.commit()
        conn.close()
        return True

    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT user_id, username, first_name, credits, referrals, referred_by, join_date, status
        FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def update_credits(self, user_id, amount, transaction_type, description):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE users SET credits = credits + ? WHERE user_id = ?
        ''', (amount, user_id))
        
        cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, description)
        VALUES (?, ?, ?, ?)
        ''', (user_id, transaction_type, amount, description))
        
        conn.commit()
        conn.close()

    def deduct_credits(self, user_id, amount):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if user has enough credits
        cursor.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result or result[0] < amount:
            conn.close()
            return False
        
        cursor.execute('''
        UPDATE users SET credits = credits - ? WHERE user_id = ?
        ''', (amount, user_id))
        
        cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, description)
        VALUES (?, ?, ?, ?)
        ''', (user_id, 'DEDUCT', -amount, 'Service usage'))
        
        conn.commit()
        conn.close()
        return True

    def generate_referral_code(self, user_id):
        raw = f"{user_id}{time.time()}"
        return hashlib.md5(raw.encode()).hexdigest()[:8].upper()

    def get_referral_code(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM referral_codes WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_user_by_referral_code(self, code):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM referral_codes WHERE code = ?", (code,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def log_service_usage(self, user_id, service_type, query):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO service_usage (user_id, service_type, query)
        VALUES (?, ?, ?)
        ''', (user_id, service_type, query))
        conn.commit()
        conn.close()

    def get_user_stats(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get total service usage
        cursor.execute('''
        SELECT COUNT(*) FROM service_usage WHERE user_id = ?
        ''', (user_id,))
        total_usage = cursor.fetchone()[0]
        
        # Get recent transactions
        cursor.execute('''
        SELECT type, amount, description, timestamp
        FROM transactions WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT 5
        ''', (user_id,))
        transactions = cursor.fetchall()
        
        conn.close()
        return {"total_usage": total_usage, "transactions": transactions}
