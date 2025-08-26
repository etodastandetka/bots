import logging
import asyncio
import sys
import platform
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Исправление для Windows и Python 3.9+
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем новую базу данных
from database_new import db_new
# Импортируем читатель баз данных ботов
from bot_database_reader import bot_db_reader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
try:
    from config import BOT_TOKENS, ADMIN_ID, API_SETTINGS
    ADMIN_BOT_TOKEN = BOT_TOKENS["admin"]
except ImportError:
    # Fallback значения если config.py не найден
    ADMIN_BOT_TOKEN = "8439194478:AAHF1VVycOeEan9HomdozJ9QfFLtglsjy_I"
    ADMIN_ID = 5474111297
    API_SETTINGS = {}

# Инициализация бота и диспетчера
bot = Bot(token=ADMIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Список ботов
BOTS = ['1xbet', 'melbet', 'mostbet']

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_admin_confirmation = State()
    waiting_for_wallet_name = State()
    waiting_for_wallet_qr_hash = State()
    waiting_for_admin_wallet_amount = State()
    waiting_for_admin_wallet_name = State()
    waiting_for_admin_wallet_bank = State()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return db_new.is_admin(user_id)

def is_main_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь главным админом"""
    return db_new.is_main_admin(user_id)

def format_statistics(stats: Dict[str, Any]) -> str:
    """Форматирует статистику для отображения"""
    text = f"📊 <b>Статистика за {stats['period']}</b>\n\n"
    
    text += f"👥 <b>Пользователи:</b>\n"
    text += f"• Всего: {stats['total_users']:,}\n"
    text += f"• Активных: {stats['active_users']:,}\n\n"
    
    text += f"💳 <b>Транзакции:</b>\n"
    text += f"• Всего: {stats['total_transactions']:,}\n"
    text += f"• Ожидают: {stats['pending_transactions']:,}\n"
    text += f"• Выполнено: {stats['completed_transactions']:,}\n"
    text += f"• Отклонено: {stats['rejected_transactions']:,}\n\n"
    
    text += f"💰 <b>Финансы:</b>\n"
    text += f"• Пополнения: {stats['deposits_count']:,} ({stats['deposits_amount']:,.2f} KGS)\n"
    text += f"• Выводы: {stats['withdrawals_count']:,} ({stats['withdrawals_amount']:,.2f} KGS)\n\n"
    
    if stats['bots_stats']:
        text += f"🤖 <b>По ботам:</b>\n"
        for bot_stat in stats['bots_stats']:
            text += f"• {bot_stat['bot_name'].upper()}: {bot_stat['total_transactions']:,} транзакций\n"
            text += f"  💰 Пополнения: {bot_stat['deposits_amount']:,.2f} KGS\n"
            text += f"  💸 Выводы: {bot_stat['withdrawals_amount']:,.2f} KGS\n\n"
    
    return text

def create_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает главную клавиатуру админа"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="💰 Кошелек")],
            [KeyboardButton(text="🏦 Баланс кассы"), KeyboardButton(text="🤖 Управление ботами")],
            [KeyboardButton(text="👥 Админы"), KeyboardButton(text="📋 Ожидающие заявки")]
        ],
        resize_keyboard=True
    )
    return keyboard

def create_statistics_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для статистики"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today"),
                InlineKeyboardButton(text="📅 Вчера", callback_data="stats_yesterday")
            ],
            [
                InlineKeyboardButton(text="📅 Неделя", callback_data="stats_week"),
                InlineKeyboardButton(text="📅 Месяц", callback_data="stats_month")
            ],
            [
                InlineKeyboardButton(text="📅 Все время", callback_data="stats_all")
            ]
        ]
    )
    return keyboard

def create_bots_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления ботами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1xbet", callback_data="bot_1xbet"),
                InlineKeyboardButton(text="1win", callback_data="bot_1win")
            ],
            [
                InlineKeyboardButton(text="Melbet", callback_data="bot_melbet"),
                InlineKeyboardButton(text="Mostbet", callback_data="bot_mostbet")
            ]
        ]
    )
    return keyboard

def create_cash_balance_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для баланса кассы"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1xbet", callback_data="balance_1xbet"),
                InlineKeyboardButton(text="1win", callback_data="balance_1win")
            ],
            [
                InlineKeyboardButton(text="Melbet", callback_data="balance_melbet"),
                InlineKeyboardButton(text="Mostbet", callback_data="balance_mostbet")
            ]
        ]
    )
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь админом
    if not is_admin(user_id):
        await message.answer("❌ У вас нет доступа к админ панели")
        return
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🔧 <b>Админ панель Lux Kassa</b>\n\n"
        "Выберите действие:"
    )
    
    await message.answer(welcome_text, reply_markup=create_main_keyboard(), parse_mode="HTML")

# Команда /admin
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    """Обработка команды /admin для получения прав админа"""
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь уже админом
    if is_admin(user_id):
        await message.answer("✅ Вы уже являетесь админом!")
        return
    
    # Проверяем, является ли пользователь главным админом
    if user_id == ADMIN_ID:
        await message.answer("✅ Вы уже являетесь главным админом!")
        return
    
    # Запрашиваем подтверждение
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="admin_confirm_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="admin_confirm_no")
            ]
        ]
    )
    
    await message.answer(
        "🤔 Вы точно хотите взять админ на себя?\n\n"
        "⚠️ Это действие требует подтверждения главного админа.",
        reply_markup=keyboard
    )
    
    await state.set_state(AdminStates.waiting_for_admin_confirmation)

# Обработка подтверждения админа
@dp.callback_query(F.data.startswith("admin_confirm_"))
async def handle_admin_confirmation(callback: types.CallbackQuery, state: FSMContext):
    """Обработка подтверждения получения прав админа"""
    if callback.data == "admin_confirm_yes":
        user_id = callback.from_user.id
        
        # Добавляем пользователя как админа
        db_new.add_admin(
            user_id=user_id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )
        
        await callback.message.edit_text("✅ Вы успешно получили права админа!")
        
        # Уведомляем главного админа
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 Новый админ: @{callback.from_user.username} (ID: {user_id})"
            )
        except:
            pass
        
    elif callback.data == "admin_confirm_no":
        await callback.message.edit_text("❌ Действие отменено")
    
    await state.clear()

# Обработка кнопки "Статистика"
@dp.message(F.text == "📊 Статистика")
async def statistics_handler(message: types.Message):
    """Обработка кнопки статистики"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return
    
    text = "📊 <b>Выберите период для статистики:</b>"
    await message.answer(text, reply_markup=create_statistics_keyboard(), parse_mode="HTML")

# Обработка статистики по периодам
@dp.callback_query(F.data.startswith("stats_"))
async def handle_statistics(callback: types.CallbackQuery):
    """Обработка статистики по периодам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    period = callback.data.replace("stats_", "")
    
    # Получаем статистику из баз данных ботов
    stats = bot_db_reader.get_all_bots_stats(period=period)
    
    # Форматируем и отправляем
    text = format_statistics(stats)
    
    await callback.message.edit_text(text, parse_mode="HTML")

# Обработка кнопки "Кошелек"
@dp.message(F.text == "💰 Кошелек")
async def wallet_handler(message: types.Message):
    """Обработка кнопки кошелька"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return
    
    # Получаем активный кошелек
    wallet = db_new.get_active_wallet()
    
    text = "💰 <b>Управление кошельками</b>\n\n"
    
    if wallet:
        text += f"💳 <b>Активный кошелек:</b>\n"
        text += f"🏦 Банк: {wallet['bank_code']}\n"
        text += f"👤 Получатель: {wallet['recipient_name'] or 'Не указан'}\n"
        text += f"💳 Сумма: {wallet['amount']:,.2f} KGS\n"
        text += f"📱 QR: {wallet['qr_hash'][:20]}...\n\n"
    else:
        text += "❌ Активный кошелек не найден\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="wallet_add")],
            [InlineKeyboardButton(text="⚙️ Выбрать активный кошелек", callback_data="wallet_list")]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка кнопки "Баланс кассы"
@dp.message(F.text == "🏦 Баланс кассы")
async def cash_balance_handler(message: types.Message):
    """Обработка кнопки баланса кассы"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return
    
    text = "🏦 <b>Выберите бота для просмотра баланса кассы:</b>"
    await message.answer(text, reply_markup=create_cash_balance_keyboard(), parse_mode="HTML")

# Обработка баланса кассы по ботам
@dp.callback_query(F.data.startswith("balance_"))
async def handle_cash_balance(callback: types.CallbackQuery):
    """Обработка баланса кассы по ботам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("balance_", "")
    
    # Получаем баланс кассы из базы данных бота
    balance = bot_db_reader.get_bot_balance(bot_name)
    
    text = f"🏦 <b>Баланс кассы {bot_name.upper()}:</b>\n\n💰 {balance:,.2f} KGS"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"balance_update_{bot_name}")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_bot_{bot_name}")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка кнопки "Управление ботами"
@dp.message(F.text == "🤖 Управление ботами")
async def bots_management_handler(message: types.Message):
    """Обработка кнопки управления ботами"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return
    
    text = "🤖 <b>Выберите бота для управления:</b>"
    await message.answer(text, reply_markup=create_bots_keyboard(), parse_mode="HTML")

# Обработка управления ботами
@dp.callback_query(F.data.startswith("bot_"))
async def handle_bot_management(callback: types.CallbackQuery):
    """Обработка управления ботами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("bot_", "")
    
    # Получаем настройки бота
    settings = db_new.get_bot_settings(bot_name)
    
    if settings:
        status_emoji = "🟢" if settings['is_active'] else "🔴"
        pause_emoji = "⏸️" if settings['is_paused'] else "▶️"
        
        text = (
            f"🤖 <b>Управление ботом {bot_name.upper()}</b>\n\n"
            f"Статус: {status_emoji} {'Активен' if settings['is_active'] else 'Неактивен'}\n"
            f"Пауза: {pause_emoji} {'На паузе' if settings['is_paused'] else 'Работает'}\n"
            f"Сообщение паузы: {settings['pause_message'] or 'Не установлено'}"
        )
    else:
        text = f"❌ Настройки для бота {bot_name.upper()} не найдены"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Активировать", callback_data=f"bot_activate_{bot_name}"),
                InlineKeyboardButton(text="🔴 Деактивировать", callback_data=f"bot_deactivate_{bot_name}")
            ],
            [
                InlineKeyboardButton(text="⏸️ Пауза", callback_data=f"bot_pause_{bot_name}"),
                InlineKeyboardButton(text="▶️ Снять паузу", callback_data=f"bot_unpause_{bot_name}")
            ],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_bot_{bot_name}")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка кнопки "Админы"
@dp.message(F.text == "👥 Админы")
async def admins_handler(message: types.Message):
    """Обработка кнопки админов"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return
    
    # Получаем всех админов
    admins = db_new.get_all_admins()
    
    if admins:
        text = "👥 <b>Список админов:</b>\n\n"
        
        for admin in admins:
            crown = "👑" if admin['is_main_admin'] else "👤"
            username = admin['username'] or "Без username"
            name = f"{admin['first_name'] or ''} {admin['last_name'] or ''}".strip() or "Не указано"
            
            text += f"{crown} <b>{username}</b>\n"
            text += f"   Имя: {name}\n"
            text += f"   ID: {admin['user_id']}\n"
            text += f"   Добавлен: {admin['created_at'][:10]}\n\n"
    else:
        text = "❌ Админы не найдены"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")],
            [InlineKeyboardButton(text="❌ Удалить админа", callback_data="admin_remove")]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка кнопки "Ожидающие заявки"
@dp.message(F.text == "📋 Ожидающие заявки")
async def pending_requests_handler(message: types.Message):
    """Обработка кнопки ожидающих заявок"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return
    
    # Получаем ожидающие транзакции из баз данных ботов
    pending_transactions = bot_db_reader.get_pending_transactions(limit=10)
    
    if pending_transactions:
        text = "📋 <b>Ожидающие заявки:</b>\n\n"
        
        for i, trans in enumerate(pending_transactions[:5], 1):
            emoji = "💳" if trans['trans_type'] == 'deposit' else "💰"
            text += f"{i}. {emoji} <b>{trans['trans_type'].title()}</b>\n"
            text += f"   Сумма: {trans['amount']:,.2f} KGS\n"
            text += f"   Бот: {trans['bot_name']}\n"
            text += f"   ID: {trans['user_id']}\n"
            text += f"   Время: {trans['created_at'][:16]}\n\n"
        
        if len(pending_transactions) > 5:
            text += f"... и еще {len(pending_transactions) - 5} заявок"
    else:
        text = "✅ Ожидающих заявок нет"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="pending_refresh")],
            [InlineKeyboardButton(text="📊 Все заявки", callback_data="pending_all")]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка обновления ожидающих заявок
@dp.callback_query(F.data == "pending_refresh")
async def handle_pending_refresh(callback: types.CallbackQuery):
    """Обработка обновления ожидающих заявок"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    # Получаем обновленные данные из баз данных ботов
    pending_transactions = bot_db_reader.get_pending_transactions(limit=10)
    
    if pending_transactions:
        text = "📋 <b>Ожидающие заявки:</b>\n\n"
        
        for i, trans in enumerate(pending_transactions[:5], 1):
            emoji = "💳" if trans['trans_type'] == 'deposit' else "💰"
            text += f"{i}. {emoji} <b>{trans['trans_type'].title()}</b>\n"
            text += f"   Сумма: {trans['amount']:,.2f} KGS\n"
            text += f"   Бот: {trans['bot_name']}\n"
            text += f"   ID: {trans['user_id']}\n"
            text += f"   Время: {trans['created_at'][:16]}\n\n"
        
        if len(pending_transactions) > 5:
            text += f"... и еще {len(pending_transactions) - 5} заявок"
    else:
        text = "✅ Ожидающих заявок нет"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="pending_refresh")],
            [InlineKeyboardButton(text="📊 Все заявки", callback_data="pending_all")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка управления статусом ботов
@dp.callback_query(F.data.startswith("bot_activate_"))
async def handle_bot_activate(callback: types.CallbackQuery):
    """Активация бота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("bot_activate_", "")
    db_new.update_bot_settings(bot_name, is_active=True, is_paused=False)
    
    await callback.answer(f"✅ Бот {bot_name.upper()} активирован")
    await handle_bot_management(callback)

@dp.callback_query(F.data.startswith("bot_deactivate_"))
async def handle_bot_deactivate(callback: types.CallbackQuery):
    """Деактивация бота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("bot_deactivate_", "")
    db_new.update_bot_settings(bot_name, is_active=False)
    
    await callback.answer(f"🔴 Бот {bot_name.upper()} деактивирован")
    await handle_bot_management(callback)

@dp.callback_query(F.data.startswith("bot_pause_"))
async def handle_bot_pause(callback: types.CallbackQuery):
    """Постановка бота на паузу"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("bot_pause_", "")
    db_new.update_bot_settings(bot_name, is_paused=True, pause_message="Бот временно отключен")
    
    await callback.answer(f"⏸️ Бот {bot_name.upper()} поставлен на паузу")
    await handle_bot_management(callback)

@dp.callback_query(F.data.startswith("bot_unpause_"))
async def handle_bot_unpause(callback: types.CallbackQuery):
    """Снятие бота с паузы"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("bot_unpause_", "")
    db_new.update_bot_settings(bot_name, is_paused=False)
    
    await callback.answer(f"▶️ Бот {bot_name.upper()} снят с паузы")
    await handle_bot_management(callback)

# Обработка обновления баланса кассы
@dp.callback_query(F.data.startswith("balance_update_"))
async def handle_balance_update(callback: types.CallbackQuery):
    """Обработка обновления баланса кассы"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("balance_update_", "")
    
    # Получаем обновленный баланс из базы данных бота
    balance = bot_db_reader.get_bot_balance(bot_name)
    
    text = f"🏦 <b>Баланс кассы {bot_name.upper()}:</b>\n\n💰 {balance:,.2f} KGS"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"balance_update_{bot_name}")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_bot_{bot_name}")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка статистики по конкретному боту
@dp.callback_query(F.data.startswith("stats_bot_"))
async def handle_bot_statistics(callback: types.CallbackQuery):
    """Обработка статистики по конкретному боту"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    bot_name = callback.data.replace("stats_bot_", "")
    
    # Получаем статистику для конкретного бота
    stats = bot_db_reader.get_bot_stats(bot_name, period="all")
    
    # Форматируем статистику
    text = f"📊 <b>Статистика бота {bot_name.upper()}</b>\n\n"
    
    text += f"👥 <b>Пользователи:</b>\n"
    text += f"• Всего: {stats['total_users']:,}\n"
    text += f"• Активных: {stats['active_users']:,}\n\n"
    
    text += f"💳 <b>Транзакции:</b>\n"
    text += f"• Всего: {stats['total_transactions']:,}\n"
    text += f"• Ожидают: {stats['pending_transactions']:,}\n"
    text += f"• Выполнено: {stats['completed_transactions']:,}\n"
    text += f"• Отклонено: {stats['rejected_transactions']:,}\n\n"
    
    text += f"💰 <b>Финансы:</b>\n"
    text += f"• Пополнения: {stats['deposits_count']:,} ({stats['deposits_amount']:,.2f} KGS)\n"
    text += f"• Выводы: {stats['withdrawals_count']:,} ({stats['withdrawals_amount']:,.2f} KGS)\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"bot_{bot_name}")],
            [InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_all")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка кошелька админа
@dp.callback_query(F.data == "admin_wallet")
async def handle_admin_wallet(callback: types.CallbackQuery):
    """Обработка кошелька админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    admin_wallet = db_new.get_admin_wallet()
    
    if admin_wallet:
        text = (
            f"👑 <b>Кошелек админа</b>\n\n"
            f"🏦 Банк: {admin_wallet['bank_code']}\n"
            f"👤 Имя: {admin_wallet['name']}\n"
            f"💳 Баланс: {admin_wallet['amount']:,.2f} KGS\n"
            f"📅 Создан: {admin_wallet['created_at'][:10]}"
        )
    else:
        text = "❌ Кошелек админа не настроен"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать кошелек", callback_data="admin_wallet_create")],
            [InlineKeyboardButton(text="💰 Изменить баланс", callback_data="admin_wallet_balance")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wallet_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка создания кошелька админа
@dp.callback_query(F.data == "admin_wallet_create")
async def handle_admin_wallet_create(callback: types.CallbackQuery, state: FSMContext):
    """Обработка создания кошелька админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    await callback.message.edit_text(
        "👑 <b>Создание кошелька админа</b>\n\n"
        "Введите название банка (например: DEMIRBANK, OPTIMABANK):",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_admin_wallet_bank)

# Обработка ввода банка для кошелька админа
@dp.message(AdminStates.waiting_for_admin_wallet_bank)
async def handle_admin_wallet_bank(message: types.Message, state: FSMContext):
    """Обработка ввода банка для кошелька админа"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        await state.clear()
        return
    
    await state.update_data(bank_code=message.text)
    
    await message.answer(
        "Теперь введите ваше имя для кошелька:",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_admin_wallet_name)

# Обработка ввода имени для кошелька админа
@dp.message(AdminStates.waiting_for_admin_wallet_name)
async def handle_admin_wallet_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени для кошелька админа"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        await state.clear()
        return
    
    data = await state.get_data()
    bank_code = data.get('bank_code')
    
    # Сохраняем кошелек админа
    db_new.save_admin_wallet(name=message.text, bank_code=bank_code)
    
    await message.answer(
        f"✅ <b>Кошелек админа создан!</b>\n\n"
        f"🏦 Банк: {bank_code}\n"
        f"👤 Имя: {message.text}\n"
        f"💳 Баланс: 0.00 KGS",
        parse_mode="HTML",
        reply_markup=create_main_keyboard()
    )
    
    await state.clear()

# Обработка изменения баланса кошелька админа
@dp.callback_query(F.data == "admin_wallet_balance")
async def handle_admin_wallet_balance(callback: types.CallbackQuery, state: FSMContext):
    """Обработка изменения баланса кошелька админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    await callback.message.edit_text(
        "💰 <b>Изменение баланса кошелька админа</b>\n\n"
        "Введите новую сумму баланса (только число):",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_admin_wallet_amount)

# Обработка ввода суммы для кошелька админа
@dp.message(AdminStates.waiting_for_admin_wallet_amount)
async def handle_admin_wallet_amount(message: types.Message, state: FSMContext):
    """Обработка ввода суммы для кошелька админа"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        await state.clear()
        return
    
    try:
        amount = float(message.text)
        if amount < 0:
            raise ValueError("Отрицательная сумма")
    except ValueError:
        await message.answer(
            "❌ Неверный формат суммы. Введите число (например: 1000.50)",
            parse_mode="HTML"
        )
        return
    
    # Обновляем баланс кошелька админа
    db_new.update_admin_wallet_amount(amount)
    
    await message.answer(
        f"✅ <b>Баланс кошелька админа обновлен!</b>\n\n"
        f"💰 Новый баланс: {amount:,.2f} KGS",
        parse_mode="HTML",
        reply_markup=create_main_keyboard()
    )
    
    await state.clear()

# Обработка возврата к кошелькам
@dp.callback_query(F.data == "wallet_back")
async def handle_wallet_back(callback: types.CallbackQuery):
    """Обработка возврата к кошелькам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    # Получаем активный кошелек
    wallet = db_new.get_active_wallet()
    
    text = "💰 <b>Управление кошельками</b>\n\n"
    
    if wallet:
        text += f"💳 <b>Активный кошелек:</b>\n"
        text += f"🏦 Банк: {wallet['bank_code']}\n"
        text += f"👤 Получатель: {wallet['recipient_name'] or 'Не указан'}\n"
        text += f"💳 Сумма: {wallet['amount']:,.2f} KGS\n"
        text += f"📱 QR: {wallet['qr_hash'][:20]}...\n\n"
    else:
        text += "❌ Активный кошелек не найден\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="wallet_add")],
            [InlineKeyboardButton(text="⚙️ Выбрать активный кошелек", callback_data="wallet_list")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка добавления кошелька
@dp.callback_query(F.data == "wallet_add")
async def handle_wallet_add(callback: types.CallbackQuery, state: FSMContext):
    """Обработка добавления кошелька"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    text = "➕ <b>Добавление нового кошелька</b>\n\n"
    text += "📝 Введите название кошелька:"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="wallet_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_wallet_name)

# Обработка списка кошельков
@dp.callback_query(F.data == "wallet_list")
async def handle_wallet_list(callback: types.CallbackQuery):
    """Обработка списка кошельков"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    # Получаем все кошельки
    wallets = db_new.get_all_wallets()
    active_wallet = db_new.get_active_wallet()
    
    if not wallets:
        text = "📋 <b>Список кошельков</b>\n\n❌ Кошельки не найдены"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="wallet_back")]
            ]
        )
    else:
        text = "📋 <b>Список кошельков</b>\n\n"
        keyboard_buttons = []
        
        for wallet in wallets:
            is_active = active_wallet and active_wallet['id'] == wallet['id']
            status_emoji = "🟢" if is_active else "⚪"
            button_text = f"{status_emoji} {wallet['name']} ({wallet['bank_code']})"
            
            if is_active:
                keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"wallet_info_{wallet['id']}")])
            else:
                keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"wallet_activate_{wallet['id']}")])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="wallet_back")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка активации кошелька
@dp.callback_query(F.data.startswith("wallet_activate_"))
async def handle_wallet_activate(callback: types.CallbackQuery):
    """Обработка активации кошелька"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    wallet_id = int(callback.data.replace("wallet_activate_", ""))
    
    # Активируем кошелек
    db_new.set_wallet_active(wallet_id, True)
    
    await callback.answer("✅ Кошелек активирован!")
    
    # Обновляем список кошельков
    await handle_wallet_list(callback)

# Обработка информации о кошельке
@dp.callback_query(F.data.startswith("wallet_info_"))
async def handle_wallet_info(callback: types.CallbackQuery):
    """Обработка информации о кошельке"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этой функции")
        return
    
    wallet_id = int(callback.data.replace("wallet_info_", ""))
    
    # Получаем информацию о кошельке
    wallets = db_new.get_all_wallets()
    wallet = next((w for w in wallets if w['id'] == wallet_id), None)
    
    if not wallet:
        await callback.answer("❌ Кошелек не найден")
        return
    
    text = f"💳 <b>Информация о кошельке</b>\n\n"
    text += f"📝 Название: {wallet['name']}\n"
    text += f"🏦 Банк: {wallet['bank_code']}\n"
    text += f"👤 Получатель: {wallet['recipient_name'] or 'Не указан'}\n"
    text += f"💳 Сумма: {wallet['amount']:,.2f} KGS\n"
    text += f"📱 QR: {wallet['qr_hash'][:20]}...\n"
    text += f"🟢 Статус: Активный"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="wallet_list")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка ввода названия кошелька
@dp.message(AdminStates.waiting_for_wallet_name)
async def handle_wallet_name(message: types.Message, state: FSMContext):
    """Обработка ввода названия кошелька"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        await state.clear()
        return
    
    await state.update_data(wallet_name=message.text)
    
    text = "📱 <b>Добавление кошелька</b>\n\n"
    text += f"📝 Название: {message.text}\n\n"
    text += "📱 Теперь введите QR-хэш кошелька:"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="wallet_back")]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_wallet_qr_hash)

# Обработка ввода QR-хэша кошелька
@dp.message(AdminStates.waiting_for_wallet_qr_hash)
async def handle_wallet_qr(message: types.Message, state: FSMContext):
    """Обработка ввода QR-хэша кошелька"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        await state.clear()
        return
    
    # Получаем данные
    data = await state.get_data()
    
    try:
        # Автоматически определяем банк из QR хэша (можно улучшить логику)
        bank_code = "OPTIMA"  # По умолчанию
        if "demir" in message.text.lower():
            bank_code = "DEMIR"
        elif "optima" in message.text.lower():
            bank_code = "OPTIMA"
        
        # Сохраняем кошелек в базу данных
        wallet_id = db_new.save_wallet(
            name=data['wallet_name'],
            qr_hash=message.text,
            bank_code=bank_code,
            recipient_name=None,
            amount=0.0
        )
        
        # Если это первый кошелек, делаем его активным
        wallets = db_new.get_all_wallets()
        if len(wallets) == 1:
            db_new.set_wallet_active(wallet_id, True)
        
        text = "✅ <b>Кошелек создан!</b>\n\n"
        text += f"📝 Название: {data['wallet_name']}\n"
        text += f"🏦 Банк: {bank_code}\n"
        text += f"📱 QR-хэш: {message.text[:30]}...\n"
        if len(wallets) == 1:
            text += f"🟢 Статус: Активный (первый кошелек)\n"
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К управлению кошельками", callback_data="wallet_back")]
            ]
        )
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка создания кошелька:</b>\n{str(e)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="wallet_back")]]
            ),
            parse_mode="HTML"
        )
    
    await state.clear()

# Удаленные неиспользуемые обработчики - теперь добавление кошелька упрощено

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск админ бота...")
    
    # Создаем базу данных если её нет
    try:
        db_new.init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        return
    
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
