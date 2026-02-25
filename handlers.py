import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Session, MenuItem, Category, NutritionalInfo
from keyboards import get_main_keyboard

# Состояния для добавления/редактирования
ADD_NAME, ADD_COMPOSITION, ADD_PRICE, ADD_CATEGORY, ADD_PHOTO, ADD_NUTRITION, ADD_RECOMMENDATIONS = range(7)
EDIT_SELECT, EDIT_FIELD, EDIT_VALUE = range(7, 10)
DELETE_SELECT = 10

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🍽 Добро пожаловать в наш ресторан!\n\n"
        "Здесь вы можете ознакомиться с меню, посмотреть состав блюд, "
        "калорийность и получить рекомендации по напиткам.\n\n"
        "Выберите интересующую вас категорию:",
        reply_markup=get_main_keyboard()
    )

async def show_breakfast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать завтраки"""
    await show_category_items(update, context, 'breakfast')

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать основное меню"""
    await show_category_items(update, context, 'main')

async def show_bar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать бар"""
    await show_category_items(update, context, 'bar')

async def show_category_items(update: Update, context: ContextTypes.DEFAULT_TYPE, category_name: str):
    """Показать блюда категории"""
    session = Session()
    category = session.query(Category).filter_by(name=category_name).first()
    
    if not category:
        await update.message.reply_text("Категория не найдена")
        session.close()
        return
    
    items = session.query(MenuItem).filter_by(
        category_id=category.id, 
        is_available=True
    ).all()
    
    if not items:
        await update.message.reply_text(
            f"В категории '{category.display_name}' пока нет блюд",
            reply_markup=get_main_keyboard()
        )
        session.close()
        return
    
    # Сохраняем items в контекст для навигации
    context.user_data['current_category'] = category_name
    context.user_data['category_items'] = [item.id for item in items]
    context.user_data['current_index'] = 0
    
    await show_menu_item(update, context, items[0])
    session.close()

async def show_menu_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item: MenuItem):
    """Показать конкретное блюдо с фото и КБЖУ"""
    session = Session()
    
    # Получаем информацию о КБЖУ
    nutritional = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
    
    # Формируем сообщение
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
        message += "\n*🍷 Рекомендации по напиткам:*\n"
        recommendations = json.loads(item.drink_recommendations)
        for rec in recommendations:
            message += f"• {rec['name']} - {rec['description']}\n"
    
    # Клавиатура для навигации
    keyboard = []
    current_index = context.user_data.get('current_index', 0)
    items_list = context.user_data.get('category_items', [])
    
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущее", callback_data="prev_item"))
    if current_index < len(items_list) - 1:
        nav_buttons.append(InlineKeyboardButton("Следующее ➡️", callback_data="next_item"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    if nutritional:
        keyboard.append([InlineKeyboardButton("📊 Детально КБЖУ", callback_data=f"nutrition_{item.id}")])
    
    keyboard.append([InlineKeyboardButton("🏠 В категории", callback_data="back_to_category")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем фото, если есть
    if item.photo_file_id:
        try:
            await update.message.reply_photo(
                photo=item.photo_file_id,
                caption=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except:
            # Если фото не загружается, отправляем без фото
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    session.close()

async def search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать поиск по меню"""
    context.user_data['search_mode'] = True
    await update.message.reply_text(
        "🔍 Введите название блюда или ключевые слова для поиска:",
        reply_markup=get_main_keyboard()
    )

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработать поисковый запрос с улучшенным поиском по ключевым словам"""
    if not context.user_data.get('search_mode'):
        return
    
    query = update.message.text.lower().strip()
    
    if not query:
        await update.message.reply_text("❌ Пожалуйста, введите поисковый запрос")
        return
    
    session = Session()
    
    # Разбиваем запрос на отдельные слова для поиска по ключевым словам
    keywords = query.split()
    
    # Создаем базовый запрос
    base_query = session.query(MenuItem).filter(MenuItem.is_available == True)
    
    # Ищем по названию и составу
    if len(keywords) > 1:
        # Если несколько ключевых слов, ищем по каждому
        from sqlalchemy import or_
        
        conditions = []
        for keyword in keywords:
            if len(keyword) > 2:  # Игнорируем очень короткие слова
                conditions.append(MenuItem.name.ilike(f'%{keyword}%'))
                conditions.append(MenuItem.composition.ilike(f'%{keyword}%'))
        
        if conditions:
            results = base_query.filter(or_(*conditions)).all()
        else:
            results = base_query.filter(
                or_(
                    MenuItem.name.ilike(f'%{query}%'),
                    MenuItem.composition.ilike(f'%{query}%')
                )
            ).all()
    else:
        # Если одно слово, ищем везде
        results = base_query.filter(
            or_(
                MenuItem.name.ilike(f'%{query}%'),
                MenuItem.composition.ilike(f'%{query}%')
            )
        ).all()
    
    if not results:
        await update.message.reply_text(
            f"😕 Ничего не найдено по запросу '{update.message.text}'. Попробуйте другие ключевые слова.",
            reply_markup=get_main_keyboard()
        )
        session.close()
        return
    
    # Сортируем результаты по релевантности (сначала точные совпадения названия)
    def relevance_score(item):
        name_lower = item.name.lower()
        # Точное совпадение названия
        if query in name_lower:
            return 3
        # Совпадение начала названия
        elif any(name_lower.startswith(k) for k in keywords if k):
            return 2
        # Частичное совпадение
        else:
            return 1
    
    results.sort(key=relevance_score, reverse=True)
    
    context.user_data['search_mode'] = False
    
    if len(results) == 1:
        # Если нашли одно блюдо, показываем его
        item = results[0]
        # Создаем временную навигацию для результата поиска
        context.user_data['category_items'] = [item.id]
        context.user_data['current_index'] = 0
        context.user_data['current_category'] = item.category.name
        await show_menu_item(update, context, item)
    else:
        # Если несколько, показываем список с релевантностью
        message = f"🔍 Найдено *{len(results)}* позиций по запросу '{update.message.text}':\n\n"
        
        for i, item in enumerate(results[:10], 1):  # Показываем только первые 10
            # Добавляем эмодзи релевантности
            if relevance_score(item) == 3:
                relevance = "🎯 "  # Точное совпадение
            elif relevance_score(item) == 2:
                relevance = "⭐ "   # Хорошее совпадение
            else:
                relevance = "• "    # Частичное совпадение
            
            message += f"{relevance}{i}. *{item.name}* - {item.price}₽\n"
        
        if len(results) > 10:
            message += f"\n... и еще {len(results) - 10} позиций"
        
        # Сохраняем результаты для последующего показа
        context.user_data['search_results'] = [item.id for item in results]
        
        # Создаем клавиатуру с кнопками для первых 10 результатов
        keyboard = []
        for i, item in enumerate(results[:10], 1):
            keyboard.append([InlineKeyboardButton(f"{i}. {item.name[:30]}...", callback_data=f"show_search_{item.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    session.close()

async def contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Контактная информация"""
    await update.message.reply_text(
        "📞 *Связаться с нами:*\n\n"
        "📍 Адрес: ул. Ресторанная, 1\n"
        "📱 Телефон: +7 (999) 123-45-67\n"
        "🕐 Часы работы: 10:00 - 23:00\n"
        "📧 Email: info@restaurant.ru\n\n"
        "🚗 Доставка работает с 11:00 до 22:00",
        parse_mode='Markdown'
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    # Очищаем все состояния
    context.user_data.clear()
    await start_command(update, context)