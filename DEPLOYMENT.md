# 🚀 Инструкция по развертыванию на Ubuntu сервере

## Предварительные требования
- Ubuntu 18.04 или новее
- Node.js 14+ (уже установлен)
- PM2 (уже установлен)

## Быстрое развертывание

### 1. Клонирование репозитория
```bash
git clone https://github.com/etodastandetka/bots.git
cd bots
```

### 2. Запуск автоматического развертывания
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Настройка конфигурации
Отредактируйте `config.py` с вашими токенами ботов:
```python
ADMIN_BOT_TOKEN = "YOUR_ADMIN_BOT_TOKEN_HERE"
ADMIN_ID = 5474111297  # Уже настроен
```

### 4. Запуск ботов
```bash
chmod +x start_bots.sh
./start_bots.sh
```

## Ручное развертывание

### 1. Установка Python и зависимостей
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Создание директории логов
```bash
mkdir -p logs
```

### 3. Запуск через PM2
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Управление ботами

### Основные команды
```bash
pm2 status          # Статус всех ботов
pm2 logs            # Логи всех ботов
pm2 restart all     # Перезапуск всех ботов
pm2 stop all        # Остановка всех ботов
pm2 delete all      # Удаление всех процессов
```

### Просмотр логов конкретного бота
```bash
pm2 logs 1xbet-bot
pm2 logs 1win-bot
pm2 logs melbet-bot
pm2 logs mostbet-bot
pm2 logs admin-bot
pm2 logs main-bot
```

### Мониторинг
```bash
pm2 monit           # Интерактивный мониторинг
pm2 show 1xbet-bot  # Детальная информация о боте
```

## Структура проекта
```
bots/
├── 1xbet.py           # Бот 1xBet
├── 1win.py            # Бот 1win
├── melbet.py          # Бот Melbet
├── mostbet.py         # Бот Mostbet
├── admin_bot.py       # Админ панель
├── main_bot.py        # Главный бот
├── config.py          # Конфигурация
├── requirements.txt   # Python зависимости
├── ecosystem.config.js # PM2 конфигурация
├── deploy.sh          # Полное развертывание
├── start_bots.sh      # Быстрый запуск
└── logs/              # Директория логов
```

## Базы данных
Все базы данных создаются автоматически при первом запуске ботов:
- `1xbet_bot.db` - база данных 1xBet бота
- `admin_bot.db` - база данных админ панели
- И другие базы для каждого бота

## Админ панель
- Главный админ ID: `5474111297`
- Доступ через админ бота с соответствующими правами

## Устранение неполадок

### Бот не запускается
```bash
pm2 logs [bot-name]    # Проверить логи
pm2 restart [bot-name] # Перезапустить бота
```

### Проблемы с зависимостями
```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Очистка PM2
```bash
pm2 delete all
pm2 kill
pm2 start ecosystem.config.js
```

## Автозапуск
PM2 автоматически запускает ботов при перезагрузке сервера благодаря команде `pm2 startup`.

## Безопасность
- Не коммитьте `config.py` с реальными токенами
- Используйте `.env` файлы для секретов
- Регулярно обновляйте зависимости
