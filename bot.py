import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from database import Session, MenuItem, Category, NutritionalInfo
from handlers import *
from admin_handlers import *
from keyboards import get_main_keyboard

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
ADD_NAME, ADD_COMPOSITION, ADD_PRICE, ADD_CATEGORY, ADD_PHOTO, ADD_NUTRITION, ADD_RECOMMENDATIONS = range(7)
EDIT_SELECT, EDIT_FIELD, EDIT_VALUE = range(7, 10)
DELETE_SELECT = 10

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на инлайн кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "prev_item":
        current_index = context.user_data.get('current_index', 0)
        if current_index > 0:
            context.user_data['current_index'] = current_index - 1
            item_id = context.user_data['category_items'][current_index - 1]
            
            session = Session()
            item = session.query(MenuItem).get(item_id)
            
            nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
            
            message = f"*{item.name}*\n\n"
            message += f"*Состав:* {item.composition}\n"
            
            if nutritional:
                message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
                message += f"🔸 Калории: {nutritional.calories} ккал\n"
                message += f"🔸 Белки: {nutritional.proteins}г\n"
                message += f"🔸 Жиры: {nutritional.fats}г\n"
                message += f"🔸 Углеводы: {nutritional.carbs}г\n"
            
            message += f"\n*💰 Цена:* {item.price}₽\n"
            
            if item.drink_recommendations:
                message += "\n*🍷 Рекомендации:*\n"
                recommendations = json.loads(item.drink_recommendations)
                for rec in recommendations:
                    message += f"• {rec['name']}\n"
            
            keyboard = []
            nav_buttons = []
            items_list = context.user_data.get('category_items', [])
            
            if context.user_data.get('current_index', 0) > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data="prev_item"))
            if context.user_data.get('current_index', 0) < len(items_list) - 1:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next_item"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            if nutritional:
                keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
            
            keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if item.photo_file_id:
                try:
                    if query.message.photo:
                        await query.edit_message_media(
                            media=InputMediaPhoto(
                                media=item.photo_file_id,
                                caption=message,
                                parse_mode='Markdown'
                            ),
                            reply_markup=reply_markup
                        )
                    else:
                        await query.message.delete()
                        await query.message.reply_photo(
                            photo=item.photo_file_id,
                            caption=message,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                except:
                    await query.edit_message_text(
                        message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            else:
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            
            session.close()
    
    elif query.data == "next_item":
        current_index = context.user_data.get('current_index', 0)
        items = context.user_data.get('category_items', [])
        if current_index < len(items) - 1:
            context.user_data['current_index'] = current_index + 1
            item_id = items[current_index + 1]
            
            session = Session()
            item = session.query(MenuItem).get(item_id)
            
            nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
            
            message = f"*{item.name}*\n\n"
            message += f"*Состав:* {item.composition}\n"
            
            if nutritional:
                message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
                message += f"🔸 Калории: {nutritional.calories} ккал\n"
                message += f"🔸 Белки: {nutritional.proteins}г\n"
                message += f"🔸 Жиры: {nutritional.fats}г\n"
                message += f"🔸 Углеводы: {nutritional.carbs}г\n"
            
            message += f"\n*💰 Цена:* {item.price}₽\n"
            
            if item.drink_recommendations:
                message += "\n*🍷 Рекомендации:*\n"
                recommendations = json.loads(item.drink_recommendations)
                for rec in recommendations:
                    message += f"• {rec['name']}\n"
            
            keyboard = []
            nav_buttons = []
            
            if context.user_data.get('current_index', 0) > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data="prev_item"))
            if context.user_data.get('current_index', 0) < len(items) - 1:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next_item"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            if nutritional:
                keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
            
            keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if item.photo_file_id:
                try:
                    if query.message.photo:
                        await query.edit_message_media(
                            media=InputMediaPhoto(
                                media=item.photo_file_id,
                                caption=message,
                                parse_mode='Markdown'
                            ),
                            reply_markup=reply_markup
                        )
                    else:
                        await query.message.delete()
                        await query.message.reply_photo(
                            photo=item.photo_file_id,
                            caption=message,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                except:
                    await query.edit_message_text(
                        message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
            else:
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            
            session.close()
    
    elif query.data.startswith("nutrition_"):
        item_id = int(query.data.split('_')[1])
        session = Session()
        
        item = session.query(MenuItem).get(item_id)
        nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item_id).first()
        
        if nutritional:
            message = f"*📊 Детальная информация о КБЖУ*\n\n"
            message += f"*{item.name}*\n"
            message += f"Вес порции: {nutritional.weight}г\n\n"
            message += f"*Калории:* {nutritional.calories} ккал\n"
            message += f"*Белки:* {nutritional.proteins}г\n"
            message += f"*Жиры:* {nutritional.fats}г\n"
            message += f"*Углеводы:* {nutritional.carbs}г\n"
            
            per_100g_cal = (nutritional.calories / nutritional.weight) * 100
            per_100g_prot = (nutritional.proteins / nutritional.weight) * 100
            per_100g_fat = (nutritional.fats / nutritional.weight) * 100
            per_100g_carbs = (nutritional.carbs / nutritional.weight) * 100
            
            message += f"\n*На 100г:*\n"
            message += f"📊 {per_100g_cal:.1f} ккал\n"
            message += f"🥩 {per_100g_prot:.1f}г белков\n"
            message += f"🧈 {per_100g_fat:.1f}г жиров\n"
            message += f"🍚 {per_100g_carbs:.1f}г углеводов"
        else:
            message = f"Информация о КБЖУ для '{item.name}' отсутствует"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад к блюду", callback_data=f"back_to_item_{item_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        session.close()
    
    elif query.data.startswith("back_to_item_"):
        item_id = int(query.data.split('_')[3])
        session = Session()
        item = session.query(MenuItem).get(item_id)
        
        nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
        
        message = f"*{item.name}*\n\n"
        message += f"*Состав:* {item.composition}\n"
        
        if nutritional:
            message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
            message += f"🔸 Калории: {nutritional.calories} ккал\n"
            message += f"🔸 Белки: {nutritional.proteins}г\n"
            message += f"🔸 Жиры: {nutritional.fats}г\n"
            message += f"🔸 Углеводы: {nutritional.carbs}г\n"
        
        message += f"\n*💰 Цена:* {item.price}₽\n"
        
        if item.drink_recommendations:
            message += "\n*🍷 Рекомендации:*\n"
            recommendations = json.loads(item.drink_recommendations)
            for rec in recommendations:
                message += f"• {rec['name']}\n"
        
        keyboard = []
        nav_buttons = []
        items_list = context.user_data.get('category_items', [])
        
        if context.user_data.get('current_index', 0) > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data="prev_item"))
        if context.user_data.get('current_index', 0) < len(items_list) - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next_item"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        if nutritional:
            keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if item.photo_file_id:
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(
                        media=item.photo_file_id,
                        caption=message,
                        parse_mode='Markdown'
                    ),
                    reply_markup=reply_markup
                )
            except:
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        session.close()
    
    elif query.data.startswith("show_search_"):
        item_id = int(query.data.split('_')[2])
        session = Session()
        item = session.query(MenuItem).get(item_id)
        
        context.user_data['category_items'] = [item_id]
        context.user_data['current_index'] = 0
        context.user_data['current_category'] = item.category.name
        
        nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
        
        message = f"*{item.name}*\n\n"
        message += f"*Состав:* {item.composition}\n"
        
        if nutritional:
            message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
            message += f"🔸 Калории: {nutritional.calories} ккал\n"
            message += f"🔸 Белки: {nutritional.proteins}г\n"
            message += f"🔸 Жиры: {nutritional.fats}г\n"
            message += f"🔸 Углеводы: {nutritional.carbs}г\n"
        
        message += f"\n*💰 Цена:* {item.price}₽\n"
        
        if item.drink_recommendations:
            message += "\n*🍷 Рекомендации:*\n"
            recommendations = json.loads(item.drink_recommendations)
            for rec in recommendations:
                message += f"• {rec['name']}\n"
        
        keyboard = []
        if nutritional:
            keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
        keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if item.photo_file_id:
            try:
                await query.message.reply_photo(
                    photo=item.photo_file_id,
                    caption=message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except:
                await query.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await query.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        await query.message.delete()
        session.close()
    
    elif query.data == "back_to_category":
        category_name = context.user_data.get('current_category')
        if category_name:
            await query.message.delete()
            if category_name == 'breakfast':
                await show_breakfast_callback(query, context)
            elif category_name == 'main':
                await show_main_menu_callback(query, context)
            elif category_name == 'bar':
                await show_bar_callback(query, context)
    
    elif query.data == "back_to_main":
        # Возврат в главное меню из поиска
        await query.message.delete()
        # Создаем фиктивное сообщение для вызова start_command
        class FakeMessage:
            def __init__(self, chat, from_user):
                self.chat = chat
                self.from_user = from_user
                self.text = "/start"
        
        fake_update = Update(update.update_id)
        fake_update.message = FakeMessage(query.message.chat, query.from_user)
        fake_update.effective_user = query.from_user
        fake_update.effective_chat = query.message.chat
        
        await start_command(fake_update, context)

async def show_breakfast_callback(query, context):
    """Показать завтраки из callback"""
    session = Session()
    category = session.query(Category).filter_by(name='breakfast').first()
    items = session.query(MenuItem).filter_by(category_id=category.id, is_available=True).all()
    
    if items:
        context.user_data['current_category'] = 'breakfast'
        context.user_data['category_items'] = [item.id for item in items]
        context.user_data['current_index'] = 0
        
        item = items[0]
        nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
        
        message = f"*{item.name}*\n\n"
        message += f"*Состав:* {item.composition}\n"
        
        if nutritional:
            message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
            message += f"🔸 Калории: {nutritional.calories} ккал\n"
            message += f"🔸 Белки: {nutritional.proteins}г\n"
            message += f"🔸 Жиры: {nutritional.fats}г\n"
            message += f"🔸 Углеводы: {nutritional.carbs}г\n"
        
        message += f"\n*💰 Цена:* {item.price}₽\n"
        
        keyboard = []
        nav_buttons = []
        if len(items) > 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next_item"))
            keyboard.append(nav_buttons)
        
        if nutritional:
            keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if item.photo_file_id:
            await query.message.reply_photo(
                photo=item.photo_file_id,
                caption=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    session.close()

async def show_main_menu_callback(query, context):
    """Показать основное меню из callback"""
    session = Session()
    category = session.query(Category).filter_by(name='main').first()
    items = session.query(MenuItem).filter_by(category_id=category.id, is_available=True).all()
    
    if items:
        context.user_data['current_category'] = 'main'
        context.user_data['category_items'] = [item.id for item in items]
        context.user_data['current_index'] = 0
        
        item = items[0]
        nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
        
        message = f"*{item.name}*\n\n"
        message += f"*Состав:* {item.composition}\n"
        
        if nutritional:
            message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
            message += f"🔸 Калории: {nutritional.calories} ккал\n"
            message += f"🔸 Белки: {nutritional.proteins}г\n"
            message += f"🔸 Жиры: {nutritional.fats}г\n"
            message += f"🔸 Углеводы: {nutritional.carbs}г\n"
        
        message += f"\n*💰 Цена:* {item.price}₽\n"
        
        keyboard = []
        nav_buttons = []
        if len(items) > 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next_item"))
            keyboard.append(nav_buttons)
        
        if nutritional:
            keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if item.photo_file_id:
            await query.message.reply_photo(
                photo=item.photo_file_id,
                caption=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    session.close()

async def show_bar_callback(query, context):
    """Показать бар из callback"""
    session = Session()
    category = session.query(Category).filter_by(name='bar').first()
    items = session.query(MenuItem).filter_by(category_id=category.id, is_available=True).all()
    
    if items:
        context.user_data['current_category'] = 'bar'
        context.user_data['category_items'] = [item.id for item in items]
        context.user_data['current_index'] = 0
        
        item = items[0]
        nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
        
        message = f"*{item.name}*\n\n"
        message += f"*Состав:* {item.composition}\n"
        
        if nutritional:
            message += f"\n*🍽 КБЖУ (на {nutritional.weight}г):*\n"
            message += f"🔸 Калории: {nutritional.calories} ккал\n"
            message += f"🔸 Белки: {nutritional.proteins}г\n"
            message += f"🔸 Жиры: {nutritional.fats}г\n"
            message += f"🔸 Углеводы: {nutritional.carbs}г\n"
        
        message += f"\n*💰 Цена:* {item.price}₽\n"
        
        keyboard = []
        nav_buttons = []
        if len(items) > 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data="next_item"))
            keyboard.append(nav_buttons)
        
        if nutritional:
            keyboard.append([InlineKeyboardButton("📊 КБЖУ", callback_data=f"nutrition_{item.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if item.photo_file_id:
            await query.message.reply_photo(
                photo=item.photo_file_id,
                caption=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    session.close()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для фото"""
    if context.user_data.get('add_state') == ADD_PHOTO:
        await add_item_photo(update, context)
    elif context.user_data.get('edit_state') == EDIT_VALUE and context.user_data.get('edit_field') == 5:
        await edit_item_value(update, context)
    else:
        await update.message.reply_text(
            "📸 Фото получено. Чтобы добавить его к блюду, войдите в режим администратора.",
            reply_markup=get_main_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик для всех текстовых сообщений"""
    text = update.message.text
    
    # Проверяем, не является ли сообщение командой или кнопкой
    if text.startswith('/'):
        return
    
    # Проверяем, не является ли сообщение кнопкой навигации
    if text in ['☀️ Завтраки', '🍽 Основное меню', '🍷 Бар', '🔍 Поиск по названию', '📞 Связаться с нами', '🏠 Главное меню',
                '➕ Добавить блюдо', '✏️ Редактировать блюдо', '❌ Удалить блюдо', '📋 Список всех блюд']:
        return
    
    # Проверяем состояние и вызываем соответствующую функцию
    add_state = context.user_data.get('add_state')
    edit_state = context.user_data.get('edit_state')
    delete_state = context.user_data.get('delete_state')
    
    # Если мы в режиме добавления
    if add_state is not None:
        if add_state == ADD_NAME:
            await add_item_name(update, context)
        elif add_state == ADD_COMPOSITION:
            await add_item_composition(update, context)
        elif add_state == ADD_PRICE:
            await add_item_price(update, context)
        elif add_state == ADD_CATEGORY:
            await add_item_category(update, context)
        elif add_state == ADD_PHOTO:
            await add_item_photo(update, context)
        elif add_state == ADD_NUTRITION:
            await add_item_nutrition(update, context)
        elif add_state == ADD_RECOMMENDATIONS:
            await add_item_recommendations(update, context)
    
    # Если мы в режиме редактирования
    elif edit_state is not None:
        if edit_state == EDIT_SELECT:
            await edit_item_select(update, context)
        elif edit_state == EDIT_FIELD:
            await edit_item_field(update, context)
        elif edit_state == EDIT_VALUE:
            await edit_item_value(update, context)
    
    # Если мы в режиме удаления
    elif delete_state is not None:
        if delete_state == DELETE_SELECT:
            await delete_item_confirm(update, context)
    
    # Если не в каком-либо режиме, то это поиск
    else:
        # Проверяем, включен ли режим поиска
        if context.user_data.get('search_mode'):
            await handle_search(update, context)

def main():
    """Главная функция запуска бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # КОМАНДЫ
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # ФОТО
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # КНОПКИ НАВИГАЦИИ (САМЫЙ ВЫСОКИЙ ПРИОРИТЕТ)
    application.add_handler(MessageHandler(filters.Regex('^☀️ Завтраки$'), show_breakfast))
    application.add_handler(MessageHandler(filters.Regex('^🍽 Основное меню$'), show_main_menu))
    application.add_handler(MessageHandler(filters.Regex('^🍷 Бар$'), show_bar))
    application.add_handler(MessageHandler(filters.Regex('^🔍 Поиск по названию$'), search_menu))
    application.add_handler(MessageHandler(filters.Regex('^📞 Связаться с нами$'), contact_us))
    application.add_handler(MessageHandler(filters.Regex('^🏠 Главное меню$'), main_menu))
    
    # АДМИНСКИЕ КНОПКИ
    application.add_handler(MessageHandler(filters.Regex('^➕ Добавить блюдо$'), add_item_start))
    application.add_handler(MessageHandler(filters.Regex('^✏️ Редактировать блюдо$'), edit_item_start))
    application.add_handler(MessageHandler(filters.Regex('^❌ Удалить блюдо$'), delete_item_start))
    application.add_handler(MessageHandler(filters.Regex('^📋 Список всех блюд$'), list_all_items))
    
    # ЕДИНЫЙ ОБРАБОТЧИК ДЛЯ ВСЕХ ОСТАЛЬНЫХ ТЕКСТОВЫХ СООБЩЕНИЙ
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Бот запущен...")
    print("📱 Откройте Telegram и найдите своего бота")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()