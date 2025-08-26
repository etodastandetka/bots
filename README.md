# Telegram Bots - Система управления ботами

## Описание
Система Telegram ботов для обработки заявок на пополнение и вывод средств.

## Боты в системе
- **1xbet-bot** - Бот для 1xBet
- **1win-bot** - Бот для 1win  
- **melbet-bot** - Бот для Melbet
- **mostbet-bot** - Бот для Mostbet
- **admin-bot** - Админ панель
- **main-bot** - Главный бот

## Быстрое развертывание на Ubuntu

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
Отредактируйте `config.py` с вашими токенами ботов.

### 4. Перезапуск ботов
```bash
pm2 restart all
```

## Управление ботами

### Основные команды PM2
```bash
pm2 status          # Статус всех ботов
pm2 logs            # Логи всех ботов
pm2 logs 1xbet-bot  # Логи конкретного бота
pm2 restart all     # Перезапуск всех ботов
pm2 stop all        # Остановка всех ботов
pm2 delete all      # Удаление всех процессов
```

### Просмотр логов
```bash
# Все логи
pm2 logs

# Конкретный бот
pm2 logs 1xbet-bot
pm2 logs 1win-bot
pm2 logs melbet-bot
pm2 logs mostbet-bot
pm2 logs admin-bot
pm2 logs main-bot
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
├── deploy.sh          # Скрипт развертывания
└── logs/              # Директория логов
```

## Требования
- Ubuntu 18.04+
- Python 3.8+
- Node.js 14+
- PM2

## Админ ID
Главный админ: `5474111297`
