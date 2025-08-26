#!/bin/bash

# Скрипт автоматического развертывания ботов на Ubuntu сервере
# Предполагается, что Node.js и PM2 уже установлены

set -e  # Остановка при ошибке

echo "🚀 Начинаем развертывание ботов..."

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка Python 3 и pip
echo "🐍 Установка Python 3 и pip..."
sudo apt install -y python3 python3-pip python3-venv

# Проверка версий
echo "✅ Проверка установленных версий:"
python3 --version
pip3 --version

# Создание директории для проекта (если не существует)
PROJECT_DIR="/home/$USER/bots"
echo "📁 Создание директории проекта: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Клонирование репозитория (если еще не склонирован)
if [ ! -d ".git" ]; then
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/etodastandetka/bots.git .
else
    echo "📥 Обновление репозитория..."
    git pull origin main
fi

# Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Обновление pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "📚 Установка Python библиотек..."
pip install -r requirements.txt

# Создание директории для логов
echo "📝 Создание директории для логов..."
mkdir -p logs

# Создание конфигурационного файла (если не существует)
if [ ! -f "config.py" ]; then
    echo "⚙️ Создание конфигурационного файла..."
    cat > config.py << 'EOF'
# Конфигурация админ-бота

# Токен админ-бота
ADMIN_BOT_TOKEN = "YOUR_ADMIN_BOT_TOKEN_HERE"

# ID главного админа
ADMIN_ID = YOUR_ADMIN_ID_HERE

# Настройки API для подключения к ботам
API_SETTINGS = {
    '1xbet': {
        'api_url': 'http://localhost:8001',
        'api_key': 'your_api_key_here'
    },
    '1win': {
        'api_url': 'http://localhost:8002', 
        'api_key': 'your_api_key_here'
    },
    'melbet': {
        'api_url': 'http://localhost:8003',
        'api_key': 'your_api_key_here'
    },
    'mostbet': {
        'api_url': 'http://localhost:8004',
        'api_key': 'your_api_key_here'
    }
}
EOF
    echo "⚠️  ВНИМАНИЕ: Отредактируйте config.py с вашими токенами!"
fi

# Установка PM2 глобально (если не установлен)
if ! command -v pm2 &> /dev/null; then
    echo "📦 Установка PM2..."
    npm install -g pm2
else
    echo "✅ PM2 уже установлен"
fi

# Остановка существующих процессов PM2
echo "🛑 Остановка существующих процессов..."
pm2 delete all 2>/dev/null || true

# Запуск ботов через PM2
echo "🚀 Запуск ботов через PM2..."
pm2 start ecosystem.config.js

# Сохранение конфигурации PM2
echo "💾 Сохранение конфигурации PM2..."
pm2 save

# Настройка автозапуска PM2
echo "🔄 Настройка автозапуска PM2..."
pm2 startup

# Проверка статуса
echo "📊 Статус процессов:"
pm2 status

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Полезные команды:"
echo "  pm2 status          - статус всех ботов"
echo "  pm2 logs            - логи всех ботов"
echo "  pm2 logs 1xbet-bot  - логи конкретного бота"
echo "  pm2 restart all     - перезапуск всех ботов"
echo "  pm2 stop all        - остановка всех ботов"
echo "  pm2 delete all      - удаление всех процессов"
echo ""
echo "⚠️  НЕ ЗАБУДЬТЕ:"
echo "  1. Отредактировать config.py с вашими токенами"
echo "  2. Перезапустить ботов: pm2 restart all"
echo ""
