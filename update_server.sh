#!/bin/bash

# Скрипт для обновления кода на сервере и перезапуска ботов
echo "🔄 Обновление кода на сервере..."

# Переходим в директорию проекта
cd /var/www/bots

# Останавливаем все боты
echo "⏹️ Останавливаем боты..."
pm2 stop all

# Обновляем код из GitHub
echo "📥 Обновляем код из GitHub..."
git pull origin master

# Обновляем зависимости если нужно
echo "📦 Обновляем зависимости..."
source venv/bin/activate
pip install -r requirements.txt

# Создаем админа если его нет
echo "👤 Проверяем админа..."
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('admin_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM admins WHERE user_id = 5474111297')
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute('''
            INSERT INTO admins (user_id, username, first_name, last_name, is_main_admin, is_active)
            VALUES (5474111297, 'operator_luxkassa', 'Operator', 'Luxkassa', TRUE, TRUE)
        ''')
        conn.commit()
        print('✅ Админ создан')
    else:
        print('✅ Админ уже существует')
    conn.close()
except Exception as e:
    print(f'❌ Ошибка: {e}')
"

# Запускаем боты
echo "🚀 Запускаем боты..."
pm2 start all

# Проверяем статус
echo "📊 Статус ботов:"
pm2 status

# Показываем логи через 5 секунд
echo "📋 Логи ботов (последние 10 строк каждого):"
sleep 5
pm2 logs --lines 10

echo "✅ Обновление завершено!"
