import sqlite3
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BotDatabaseReader:
    def __init__(self):
        self.bot_dbs = {
            '1xbet': '1xbet_bot.db',
            '1win': '1win_bot.db', 
            'melbet': 'melbet_bot.db',
            'mostbet': 'mostbet_bot.db'
        }
    
    def get_bot_statistics(self, bot_name: str) -> Dict[str, Any]:
        """Получает статистику конкретного бота"""
        try:
            db_path = self.bot_dbs.get(bot_name)
            if not db_path:
                return {}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Получаем статистику пользователей
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE active = 1')
            active_users = cursor.fetchone()[0] or 0
            
            # Получаем статистику транзакций
            cursor.execute('SELECT COUNT(*) FROM transactions')
            total_transactions = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "pending"')
            pending_transactions = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "completed"')
            completed_transactions = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "rejected"')
            rejected_transactions = cursor.fetchone()[0] or 0
            
            # Получаем статистику по суммам
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE type = "deposit" AND status = "completed"')
            deposits_result = cursor.fetchone()
            deposits_count = deposits_result[0] or 0
            deposits_amount = deposits_result[1] or 0
            
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE type = "withdrawal" AND status = "completed"')
            withdrawals_result = cursor.fetchone()
            withdrawals_count = withdrawals_result[0] or 0
            withdrawals_amount = withdrawals_result[1] or 0
            
            conn.close()
            
            return {
                'bot_name': bot_name,
                'total_users': total_users,
                'active_users': active_users,
                'total_transactions': total_transactions,
                'pending_transactions': pending_transactions,
                'completed_transactions': completed_transactions,
                'rejected_transactions': rejected_transactions,
                'deposits_count': deposits_count,
                'deposits_amount': deposits_amount,
                'withdrawals_count': withdrawals_count,
                'withdrawals_amount': withdrawals_amount
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики для {bot_name}: {e}")
            return {
                'bot_name': bot_name,
                'total_users': 0,
                'active_users': 0,
                'total_transactions': 0,
                'pending_transactions': 0,
                'completed_transactions': 0,
                'rejected_transactions': 0,
                'deposits_count': 0,
                'deposits_amount': 0,
                'withdrawals_count': 0,
                'withdrawals_amount': 0
            }
    
    def get_all_bots_statistics(self) -> List[Dict[str, Any]]:
        """Получает статистику всех ботов"""
        stats = []
        for bot_name in self.bot_dbs.keys():
            bot_stats = self.get_bot_statistics(bot_name)
            if bot_stats:
                stats.append(bot_stats)
        return stats
    
    def get_pending_requests(self, bot_name: str = None) -> List[Dict[str, Any]]:
        """Получает ожидающие заявки"""
        try:
            requests = []
            
            if bot_name:
                # Получаем заявки конкретного бота
                db_path = self.bot_dbs.get(bot_name)
                if db_path:
                    requests.extend(self._get_pending_from_db(db_path, bot_name))
            else:
                # Получаем заявки всех ботов
                for bot_name, db_path in self.bot_dbs.items():
                    requests.extend(self._get_pending_from_db(db_path, bot_name))
            
            return requests
            
        except Exception as e:
            logger.error(f"Ошибка получения ожидающих заявок: {e}")
            return []
    
    def _get_pending_from_db(self, db_path: str, bot_name: str) -> List[Dict[str, Any]]:
        """Получает ожидающие заявки из конкретной базы данных"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, amount, type, status, created_at, bank_name, wallet_number
                FROM transactions 
                WHERE status = "pending"
                ORDER BY created_at DESC
                LIMIT 10
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            requests = []
            for row in rows:
                requests.append({
                    'id': row[0],
                    'user_id': row[1],
                    'amount': row[2],
                    'type': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'bank_name': row[6],
                    'wallet_number': row[7],
                    'bot_name': bot_name
                })
            
            return requests
            
        except Exception as e:
            logger.error(f"Ошибка получения заявок из {db_path}: {e}")
            return []

# Создаем экземпляр читателя баз данных
bot_db_reader = BotDatabaseReader()
