import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

class Database:
    def __init__(self, db_path: str = 'admin_bot.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных для админ бота"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу ботов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_source TEXT UNIQUE,
            bot_name TEXT,
            bot_token TEXT,
            admin_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            is_paused BOOLEAN DEFAULT 0,
            pause_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Создаем таблицу пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xbet_id TEXT,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language TEXT DEFAULT 'ru',
            bot_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Создаем таблицу транзакций
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trans_type TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            bank_details TEXT,
            recipient_name TEXT,
            receipt_file_id TEXT,
            qr_file_id TEXT,
            xbet_id TEXT,
            first_name TEXT,
            last_name TEXT,
            bot_source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Создаем таблицу чатов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            admin_id INTEGER,
            message_text TEXT,
            is_from_user BOOLEAN,
            message_id INTEGER,
            reply_to_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Создаем таблицу кошельков
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            qr_hash TEXT,
            bank_code TEXT,
            recipient_name TEXT,
            amount REAL DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Создаем таблицу уведомлений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            message TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_statistics(self, period: str = "all") -> Dict[str, Any]:
        """Получить общую статистику с фильтрацией по периоду"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Определяем временной фильтр
        if period == "today":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = datetime.now() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = None
        
        # Базовые запросы
        if start_date:
            cursor.execute('SELECT COUNT(*) FROM users WHERE created_at >= ?', (start_date,))
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM transactions WHERE created_at >= ?', (start_date,))
            active_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE created_at >= ?', (start_date,))
            total_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "pending" AND created_at >= ?', (start_date,))
            pending_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "confirmed" AND created_at >= ?', (start_date,))
            completed_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "rejected" AND created_at >= ?', (start_date,))
            rejected_transactions = cursor.fetchone()[0]
            
            # Статистика по депозитам
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE trans_type = "deposit" AND status = "confirmed" AND created_at >= ?', (start_date,))
            deposits_result = cursor.fetchone()
            deposits_count = deposits_result[0] or 0
            deposits_amount = deposits_result[1] or 0
            
            # Статистика по выводам
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE trans_type = "withdraw" AND status = "confirmed" AND created_at >= ?', (start_date,))
            withdrawals_result = cursor.fetchone()
            withdrawals_count = withdrawals_result[0] or 0
            withdrawals_amount = withdrawals_result[1] or 0
            
        else:
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM transactions WHERE created_at >= ?', (thirty_days_ago,))
            active_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions')
            total_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "pending"')
            pending_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "confirmed"')
            completed_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "rejected"')
            rejected_transactions = cursor.fetchone()[0]
            
            # Статистика по депозитам
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE trans_type = "deposit" AND status = "confirmed"')
            deposits_result = cursor.fetchone()
            deposits_count = deposits_result[0] or 0
            deposits_amount = deposits_result[1] or 0
            
            # Статистика по выводам
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE trans_type = "withdraw" AND status = "confirmed"')
            withdrawals_result = cursor.fetchone()
            withdrawals_count = withdrawals_result[0] or 0
            withdrawals_amount = withdrawals_result[1] or 0
        
        # Статистика по ботам
        cursor.execute('''
        SELECT bot_source, 
               COUNT(CASE WHEN trans_type = 'deposit' AND status = 'confirmed' THEN 1 END) as deposits_count,
               SUM(CASE WHEN trans_type = 'deposit' AND status = 'confirmed' THEN amount ELSE 0 END) as deposits_amount,
               COUNT(CASE WHEN trans_type = 'withdraw' AND status = 'confirmed' THEN 1 END) as withdrawals_count,
               SUM(CASE WHEN trans_type = 'withdraw' AND status = 'confirmed' THEN amount ELSE 0 END) as withdrawals_amount
        FROM transactions 
        WHERE bot_source IS NOT NULL
        GROUP BY bot_source
        ''')
        
        bots_stats = []
        for row in cursor.fetchall():
            bots_stats.append({
                'bot_source': row[0],
                'deposits_count': row[1] or 0,
                'deposits_amount': row[2] or 0,
                'withdrawals_count': row[3] or 0,
                'withdrawals_amount': row[4] or 0
            })
        
        conn.close()
        
        return {
            'period': period,
            'total_users': total_users,
            'active_users': active_users,
            'total_transactions': total_transactions,
            'pending_transactions': pending_transactions,
            'completed_transactions': completed_transactions,
            'rejected_transactions': rejected_transactions,
            'deposits_count': deposits_count,
            'deposits_amount': deposits_amount,
            'withdrawals_count': withdrawals_count,
            'withdrawals_amount': withdrawals_amount,
            'bots_stats': bots_stats
        }
    
    def get_all_bots_status(self) -> List[Dict[str, Any]]:
        """Получить статус всех ботов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT bot_source, bot_name, is_active, is_paused, pause_message 
        FROM bots
        ''')
        
        bots = []
        for row in cursor.fetchall():
            bots.append({
                'bot_source': row[0],
                'bot_name': row[1],
                'is_active': bool(row[2]),
                'is_paused': bool(row[3]),
                'pause_message': row[4]
            })
        
        conn.close()
        return bots
    
    def set_bot_status(self, bot_source: str, is_active: bool = True, is_paused: bool = False, pause_message: str = None):
        """Установить статус бота"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO bots (bot_source, is_active, is_paused, pause_message)
        VALUES (?, ?, ?, ?)
        ''', (bot_source, is_active, is_paused, pause_message))
        
        conn.commit()
        conn.close()
    
    def get_users_count(self) -> int:
        """Получить общее количество пользователей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_active_users_count(self, days: int = 30) -> int:
        """Получить количество активных пользователей за указанное количество дней"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        days_ago = datetime.now() - timedelta(days=days)
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM transactions WHERE created_at >= ?', (days_ago,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_pending_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить ожидающие транзакции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, user_id, trans_type, amount, status, xbet_id, first_name, last_name, bot_source, created_at
        FROM transactions 
        WHERE status = 'pending'
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'user_id': row[1],
                'trans_type': row[2],
                'amount': row[3],
                'status': row[4],
                'xbet_id': row[5],
                'first_name': row[6],
                'last_name': row[7],
                'bot_source': row[8],
                'created_at': row[9]
            })
        
        conn.close()
        return transactions
    
    def get_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Получить транзакцию по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, user_id, trans_type, amount, status, xbet_id, first_name, last_name, bot_source, created_at
        FROM transactions 
        WHERE id = ?
        ''', (transaction_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'trans_type': row[2],
                'amount': row[3],
                'status': row[4],
                'xbet_id': row[5],
                'first_name': row[6],
                'last_name': row[7],
                'bot_source': row[8],
                'created_at': row[9]
            }
        return None
    
    def update_transaction_status(self, transaction_id: int, status: str):
        """Обновить статус транзакции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE transactions SET status = ? WHERE id = ?', (status, transaction_id))
        
        conn.commit()
        conn.close()
    
    def save_chat_message(self, user_id: int, admin_id: int, message_text: str, is_from_user: bool, message_id: int = None, reply_to_message_id: int = None):
        """Сохранить сообщение чата"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO chat_messages (user_id, admin_id, message_text, is_from_user, message_id, reply_to_message_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, admin_id, message_text, is_from_user, message_id, reply_to_message_id))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить историю чата с пользователем"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT message_text, is_from_user, created_at
        FROM chat_messages 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        ''', (user_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message_text': row[0],
                'is_from_user': bool(row[1]),
                'created_at': row[2]
            })
        
        conn.close()
        return messages
    
    def save_wallet(self, name: str, qr_hash: str, bank_code: str, recipient_name: str = None, amount: float = 0.0) -> int:
        """Сохранить кошелек"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO wallets (name, qr_hash, bank_code, recipient_name, amount)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, qr_hash, bank_code, recipient_name, amount))
        
        wallet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return wallet_id
    
    def get_active_wallet(self) -> Optional[Dict[str, Any]]:
        """Получить активный кошелек"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, qr_hash, bank_code, recipient_name, amount
        FROM wallets 
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'qr_hash': row[2],
                'bank_code': row[3],
                'recipient_name': row[4],
                'amount': row[5]
            }
        return None
    
    def get_all_wallets(self) -> List[Dict[str, Any]]:
        """Получить все кошельки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, name, qr_hash, bank_code, recipient_name, amount, is_active, created_at
        FROM wallets
        ORDER BY created_at DESC
        ''')
        
        wallets = []
        for row in cursor.fetchall():
            wallets.append({
                'id': row[0],
                'name': row[1],
                'qr_hash': row[2],
                'bank_code': row[3],
                'recipient_name': row[4],
                'amount': row[5],
                'is_active': bool(row[6]),
                'created_at': row[7]
            })
        
        conn.close()
        return wallets
    
    def update_wallet_amount(self, wallet_id: int, new_amount: float):
        """Обновить сумму кошелька"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE wallets SET amount = ? WHERE id = ?', (new_amount, wallet_id))
        
        conn.commit()
        conn.close()
    
    def set_wallet_active(self, wallet_id: int, is_active: bool = True):
        """Установить кошелек как активный/неактивный"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if is_active:
            # Деактивируем все кошельки
            cursor.execute('UPDATE wallets SET is_active = 0')
        
        # Активируем выбранный кошелек
        cursor.execute('UPDATE wallets SET is_active = ? WHERE id = ?', (is_active, wallet_id))
        
        conn.commit()
        conn.close()

# Создаем глобальный экземпляр базы данных
db = Database() 