import sqlite3
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class DatabaseNew:
    def __init__(self, db_path: str = 'admin_bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создание таблицы админов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_main_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание таблицы кошельков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    bank TEXT NOT NULL,
                    qr_hash TEXT,
                    amount REAL DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание таблицы статистики
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY,
                    date DATE NOT NULL,
                    bot_name TEXT NOT NULL,
                    total_transactions INTEGER DEFAULT 0,
                    deposits_count INTEGER DEFAULT 0,
                    deposits_amount REAL DEFAULT 0,
                    withdrawals_count INTEGER DEFAULT 0,
                    withdrawals_amount REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("База данных admin_bot.db инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT is_active FROM admins WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0]
        except Exception as e:
            logger.error(f"Ошибка проверки админа: {e}")
            return False
    
    def is_main_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь главным админом"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT is_main_admin FROM admins WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None and result[0]
        except Exception as e:
            logger.error(f"Ошибка проверки главного админа: {e}")
            return False
    
    def add_admin(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, is_main: bool = False):
        """Добавляет нового админа"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO admins (user_id, username, first_name, last_name, is_main_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, is_main))
            conn.commit()
            conn.close()
            logger.info(f"Админ {user_id} добавлен/обновлен")
        except Exception as e:
            logger.error(f"Ошибка добавления админа: {e}")
    
    def get_statistics(self, period: str = 'today') -> Dict[str, Any]:
        """Получает статистику за период"""
        # Заглушка для статистики
        return {
            'period': period,
            'total_users': 1000,
            'active_users': 500,
            'total_transactions': 2500,
            'pending_transactions': 50,
            'completed_transactions': 2400,
            'rejected_transactions': 50,
            'deposits_count': 1500,
            'deposits_amount': 1500000.0,
            'withdrawals_count': 1000,
            'withdrawals_amount': 1000000.0,
            'bots_stats': [
                {
                    'bot_name': '1xbet',
                    'total_transactions': 800,
                    'deposits_amount': 500000.0,
                    'withdrawals_amount': 300000.0
                },
                {
                    'bot_name': '1win',
                    'total_transactions': 600,
                    'deposits_amount': 400000.0,
                    'withdrawals_amount': 250000.0
                }
            ]
        }
    
    def save_wallet(self, name: str, qr_hash: str, bank_code: str, recipient_name: str = None, amount: float = 0.0) -> int:
        """Сохраняет кошелек в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO wallets (name, bank, qr_hash, amount)
                VALUES (?, ?, ?, ?)
            ''', (name, bank_code, qr_hash, amount))
            wallet_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Кошелек {name} сохранен с ID {wallet_id}")
            return wallet_id
        except Exception as e:
            logger.error(f"Ошибка сохранения кошелька: {e}")
            return 0
    
    def get_all_wallets(self) -> List[Dict[str, Any]]:
        """Получает все кошельки"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, bank, qr_hash, amount, is_active FROM wallets')
            rows = cursor.fetchall()
            conn.close()
            
            wallets = []
            for row in rows:
                wallets.append({
                    'id': row[0],
                    'name': row[1],
                    'bank': row[2],
                    'qr_hash': row[3],
                    'amount': row[4],
                    'is_active': row[5]
                })
            return wallets
        except Exception as e:
            logger.error(f"Ошибка получения кошельков: {e}")
            return []
    
    def set_wallet_active(self, wallet_id: int, is_active: bool) -> bool:
        """Устанавливает активность кошелька"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE wallets SET is_active = ? WHERE id = ?', (is_active, wallet_id))
            conn.commit()
            conn.close()
            logger.info(f"Кошелек {wallet_id} установлен как {'активный' if is_active else 'неактивный'}")
            return True
        except Exception as e:
            logger.error(f"Ошибка установки активности кошелька: {e}")
            return False

# Создаем экземпляр базы данных
db_new = DatabaseNew()
