from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import CATEGORIES

def get_main_keyboard():
    """Основная клавиатура с категориями"""
    keyboard = [
        [KeyboardButton(CATEGORIES['breakfast'])],
        [KeyboardButton(CATEGORIES['main'])],
        [KeyboardButton(CATEGORIES['bar'])],
        [KeyboardButton('🔍 Поиск по названию')],
        [KeyboardButton('📞 Связаться с нами')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    """Клавиатура для администратора"""
    keyboard = [
        [KeyboardButton('➕ Добавить блюдо')],
        [KeyboardButton('✏️ Редактировать блюдо')],
        [KeyboardButton('❌ Удалить блюдо')],
        [KeyboardButton('📋 Список всех блюд')],
        [KeyboardButton('🏠 Главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [KeyboardButton('🔙 Назад')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)