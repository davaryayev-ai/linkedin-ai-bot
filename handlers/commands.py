from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Анализ поста")],
            [KeyboardButton(text="✍️ Сгенерировать пост")],
            [KeyboardButton(text="📰 Новости n8n & AI")]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "Привет! Я твой личный ИИ-ассистент для LinkedIn. 🚀\n\n"
        "Я помогу тебе анализировать твои посты, запоминать успешные паттерны "
        "и генерировать новые крутые тексты.\n\n"
        "Выбери действие в меню ниже:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "Доступные команды:\n"
        "/start - Перезапустить бота\n"
        "/cancel - Отменить текущее действие\n"
        "/analyze - Начать анализ поста\n"
        "/news - Получить свежие новости AI & n8n\n"
    )
    await message.answer(help_text)
