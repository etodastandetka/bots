#!/bin/bash

echo "🔧 Исправление зависимостей..."

# Остановить боты
echo "🛑 Остановка ботов..."
pm2 stop all

# Активировать виртуальное окружение
echo "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Удалить проблемные пакеты
echo "🗑️ Удаление проблемных пакетов..."
pip uninstall -y aiogram aiohttp pydantic

# Установить стабильные версии
echo "📦 Установка стабильных версий..."
pip install -r requirements.txt

# Проверить установку
echo "✅ Проверка установки..."
python -c "import aiogram; print(f'aiogram version: {aiogram.__version__}')"
python -c "import aiohttp; print(f'aiohttp version: {aiohttp.__version__}')"

# Запустить боты
echo "🚀 Запуск ботов..."
pm2 start all

# Показать статус
echo "📊 Статус ботов:"
pm2 status

echo "✅ Зависимости исправлены!"
