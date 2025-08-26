import logging
import asyncio
from typing import Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
try:
    from config import BOT_TOKENS, CHANNEL_LINK
    BOT_TOKEN = BOT_TOKENS["main"]
except ImportError:
    BOT_TOKEN = "8206205994:AAE00qmtzbMQbQJRzuwKLeTkAbKf8ZNtC0Q"
    CHANNEL_LINK = "https://t.me/luxkassa_news"
except Exception as e:
    print(f"Ошибка загрузки конфигурации: {e}")
    BOT_TOKEN = "8206205994:AAE00qmtzbMQbQJRzuwKLeTkAbKf8ZNtC0Q"
    CHANNEL_LINK = "https://t.me/luxkassa_news"

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Языки пользователей
user_languages: Dict[int, str] = {}

# Переводы
translations = {
    'ru': {
        'welcome': "👋 Привет, {username}!\n\n"
                   "📥 Пополнение - 0%\n"
                   "📤 Вывод - 0%\n\n"
                   "⚡️ Пополнение: от 35 с до 100 000 с\n"
                   "🚀 Вывод: без ограничений\n\n"
                   "👨‍💻 Поддержка: @operator_luxkassa\n"
                   "💬 Наш чат: @luxkassa_chat\n\n"
                   "🔒 Все транзакции под контролем опытной финансовой команды",
        'channel': "📢 Канал",
        'language': "🌐 Язык"
    },
    'ky': {
        'welcome': "👋 Салам, {username}!\n\n"
                   "📥 Толтуруу - 0%\n"
                   "📤 Чыгаруу - 0%\n\n"
                   "⚡️ Толтуруу: 35 с ден 100 000 с чейин\n"
                   "🚀 Чыгаруу: чектөөсүз\n\n"
                   "👨‍💻 Колдоо: @operator_luxkassa\n"
                   "💬 Биздин чат: @luxkassa_chat\n\n"
                   "🔒 Бардык транзакциялар тажрыйбалуу каржы командасынын көзөмөлүндө",
        'channel': "📢 Канал",
        'language': "🌐 Тил"
    },
    'uz': {
        'welcome': "👋 Salom, {username}!\n\n"
                   "📥 To'ldirish - 0%\n"
                   "📤 Chiqarish - 0%\n\n"
                   "⚡️ To'ldirish: 35 s dan 100 000 s gacha\n"
                   "🚀 Chiqarish: cheklovsiz\n\n"
                   "👨‍💻 Qo'llab-quvvatlash: @operator_luxkassa\n"
                   "💬 Bizning chat: @luxkassa_chat\n\n"
                   "🔒 Barcha tranzaktsiyalar tajribali moliyaviy jamoaning nazorati ostida",
        'channel': "📢 Kanal",
        'language': "🌐 Til"
    }
}

def get_text(user_id: int, key: str, username: str = "пользователь") -> str:
    lang = user_languages.get(user_id, 'ru')
    text = translations.get(lang, translations['ru']).get(key, key)
    return text.format(username=username)

def get_main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="1XBET", url="https://t.me/xLuxkassa_bot"),
        InlineKeyboardButton(text="1WIN", url="https://t.me/wluxkassa_bot")
    )
    kb.row(
        InlineKeyboardButton(text="MELBET", url="https://t.me/mluxkassa_bot"),
        InlineKeyboardButton(text="MOSTBET", url="https://t.me/sluxkassa_bot")
    )
    kb.row(
        InlineKeyboardButton(text=get_text(user_id, 'channel'), url=CHANNEL_LINK),
        InlineKeyboardButton(text=get_text(user_id, 'language'), callback_data="change_language")
    )
    
    return kb.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_languages.setdefault(user_id, 'ru')
    
    # Получаем имя пользователя
    username = message.from_user.first_name or "пользователь"
    
    await message.answer(
        get_text(user_id, 'welcome', username),
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "change_language")
async def change_language_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current = user_languages.get(user_id, 'ru')
    # Циклическое переключение между языками: ru -> ky -> uz -> ru
    if current == 'ru':
        new_lang = 'ky'
        message = "✅ Тил кыргызчага өзгөртүлдү"
    elif current == 'ky':
        new_lang = 'uz'
        message = "✅ Til o'zbekchaga o'zgartirildi"
    else:
        new_lang = 'ru'
        message = "✅ Язык изменен на русский"
    
    user_languages[user_id] = new_lang
    
    # Получаем имя пользователя
    username = callback.from_user.first_name or "пользователь"
    
    # Обновляем сообщение с новым языком
    await callback.message.edit_text(
        get_text(user_id, 'welcome', username),
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode="HTML"
    )
    
    # Показываем уведомление о смене языка
    await callback.answer(message)

async def main():
    logger.info("🚀 Запуск бота Lux Kassa...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
