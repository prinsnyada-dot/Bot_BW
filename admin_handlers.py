import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Session, MenuItem, Category, NutritionalInfo
from config import ADMIN_IDS
from keyboards import get_admin_keyboard, get_main_keyboard

# Состояния для добавления/редактирования
ADD_NAME, ADD_COMPOSITION, ADD_PRICE, ADD_CATEGORY, ADD_PHOTO, ADD_NUTRITION, ADD_RECOMMENDATIONS = range(7)
EDIT_SELECT, EDIT_FIELD, EDIT_VALUE = range(7, 10)
DELETE_SELECT = 10

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вход в админ-панель"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав администратора")
        return
    
    context.user_data['admin_mode'] = True
    context.user_data['in_admin_panel'] = True
    await update.message.reply_text(
        "🔐 *Режим администратора*\n\n"
        "Выберите действие:",
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )

# ===================== ДОБАВЛЕНИЕ БЛЮДА =====================

async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление нового блюда"""
    if not context.user_data.get('admin_mode'):
        return
    
    context.user_data['add_state'] = ADD_NAME
    context.user_data['in_add_mode'] = True
    await update.message.reply_text(
        "📝 Введите название блюда:"
    )

async def add_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название блюда"""
    # Проверяем, что мы действительно в состоянии добавления названия
    if context.user_data.get('add_state') != ADD_NAME:
        return
    
    # Сохраняем название
    context.user_data['new_item'] = {'name': update.message.text}
    context.user_data['add_state'] = ADD_COMPOSITION
    
    await update.message.reply_text(
        "📋 Введите состав блюда:"
    )

async def add_item_composition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить состав блюда"""
    # Проверяем, что мы действительно в состоянии добавления состава
    if context.user_data.get('add_state') != ADD_COMPOSITION:
        return
    
    # Сохраняем состав
    context.user_data['new_item']['composition'] = update.message.text
    context.user_data['add_state'] = ADD_PRICE
    
    await update.message.reply_text(
        "💰 Введите цену (только число):"
    )

async def add_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить цену"""
    # Проверяем, что мы действительно в состоянии добавления цены
    if context.user_data.get('add_state') != ADD_PRICE:
        return
    
    try:
        price = float(update.message.text)
        context.user_data['new_item']['price'] = price
        context.user_data['add_state'] = ADD_CATEGORY
        
        # Показываем доступные категории
        session = Session()
        categories = session.query(Category).all()
        session.close()
        
        categories_text = "📁 Выберите категорию (введите номер):\n"
        for cat in categories:
            categories_text += f"{cat.id}. {cat.display_name}\n"
        
        await update.message.reply_text(categories_text)
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите корректное число (например: 450)"
        )

async def add_item_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить категорию"""
    # Проверяем, что мы действительно в состоянии выбора категории
    if context.user_data.get('add_state') != ADD_CATEGORY:
        return
    
    try:
        category_id = int(update.message.text)
        session = Session()
        category = session.query(Category).get(category_id)
        
        if not category:
            await update.message.reply_text("❌ Категория не найдена. Попробуйте снова:")
            session.close()
            return
        
        context.user_data['new_item']['category_id'] = category_id
        context.user_data['add_state'] = ADD_PHOTO
        
        await update.message.reply_text(
            "📸 Отправьте фото блюда (или отправьте 'пропустить' если фото нет):"
        )
        session.close()
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите номер категории (1, 2 или 3):"
        )

async def add_item_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить фото блюда"""
    # Проверяем, что мы действительно в состоянии добавления фото
    if context.user_data.get('add_state') != ADD_PHOTO:
        return
    
    if update.message.photo:
        # Получаем file_id самого большого фото
        photo = update.message.photo[-1]
        context.user_data['new_item']['photo_file_id'] = photo.file_id
        await update.message.reply_text("✅ Фото получено!")
    elif update.message.text and update.message.text.lower() == 'пропустить':
        context.user_data['new_item']['photo_file_id'] = None
        await update.message.reply_text("⏭ Фото пропущено")
    else:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте фото или напишите 'пропустить'"
        )
        return
    
    context.user_data['add_state'] = ADD_NUTRITION
    await update.message.reply_text(
        "📊 Введите информацию о КБЖУ в формате:\n"
        "вес(г),калории,белки,жиры,углеводы\n"
        "Например: 250,350,15,12,40\n"
        "Или отправьте 'пропустить' если информации нет"
    )

async def add_item_nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить информацию о КБЖУ"""
    # Проверяем, что мы действительно в состоянии добавления КБЖУ
    if context.user_data.get('add_state') != ADD_NUTRITION:
        return
    
    if update.message.text and update.message.text.lower() != 'пропустить':
        try:
            parts = update.message.text.split(',')
            if len(parts) != 5:
                raise ValueError("Нужно 5 значений")
            
            weight, calories, proteins, fats, carbs = map(float, parts)
            context.user_data['new_item']['nutrition'] = {
                'weight': weight,
                'calories': calories,
                'proteins': proteins,
                'fats': fats,
                'carbs': carbs
            }
            await update.message.reply_text("✅ Данные КБЖУ сохранены")
        except:
            await update.message.reply_text(
                "❌ Неверный формат. Пожалуйста, введите данные в формате: вес,калории,белки,жиры,углеводы\n"
                "Например: 250,350,15,12,40"
            )
            return
    else:
        context.user_data['new_item']['nutrition'] = None
        if update.message.text and update.message.text.lower() == 'пропустить':
            await update.message.reply_text("⏭ КБЖУ пропущено")
    
    context.user_data['add_state'] = ADD_RECOMMENDATIONS
    await update.message.reply_text(
        "🍷 Введите рекомендации по напиткам в формате:\n"
        "Название напитка: описание\n"
        "Каждая рекомендация с новой строки\n"
        "Например:\n"
        "Апероль Шприц: легкий аперитив с апельсином\n"
        "Если рекомендаций нет, отправьте 'нет'"
    )

async def add_item_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить рекомендации и сохранить блюдо"""
    # Проверяем, что мы действительно в состоянии добавления рекомендаций
    if context.user_data.get('add_state') != ADD_RECOMMENDATIONS:
        return
    
    recommendations = []
    if update.message.text.lower() != 'нет':
        lines = update.message.text.split('\n')
        for line in lines:
            if ':' in line:
                name, desc = line.split(':', 1)
                recommendations.append({
                    'name': name.strip(),
                    'description': desc.strip()
                })
        await update.message.reply_text(f"✅ Получено {len(recommendations)} рекомендаций")
    else:
        await update.message.reply_text("⏭ Рекомендации пропущены")
    
    # Сохраняем в базу
    session = Session()
    new_item = MenuItem(
        name=context.user_data['new_item']['name'],
        composition=context.user_data['new_item']['composition'],
        price=context.user_data['new_item']['price'],
        category_id=context.user_data['new_item']['category_id'],
        photo_file_id=context.user_data['new_item'].get('photo_file_id'),
        drink_recommendations=json.dumps(recommendations, ensure_ascii=False),
        is_available=True
    )
    
    session.add(new_item)
    session.flush()  # Чтобы получить id нового блюда
    
    # Добавляем информацию о КБЖУ
    if context.user_data['new_item'].get('nutrition'):
        nutrition = NutritionalInfo(
            menu_item_id=new_item.id,
            weight=context.user_data['new_item']['nutrition']['weight'],
            calories=context.user_data['new_item']['nutrition']['calories'],
            proteins=context.user_data['new_item']['nutrition']['proteins'],
            fats=context.user_data['new_item']['nutrition']['fats'],
            carbs=context.user_data['new_item']['nutrition']['carbs']
        )
        session.add(nutrition)
    
    session.commit()
    session.close()
    
    # Очищаем состояние добавления
    context.user_data.pop('add_state', None)
    context.user_data.pop('new_item', None)
    context.user_data.pop('in_add_mode', None)
    
    await update.message.reply_text(
        "✅ Блюдо успешно добавлено!",
        reply_markup=get_admin_keyboard()
    )

# ===================== ПРОСМОТР ВСЕХ БЛЮД =====================

async def list_all_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все блюда в меню"""
    if not context.user_data.get('admin_mode'):
        return
    
    session = Session()
    items = session.query(MenuItem).filter_by(is_available=True).all()
    
    if not items:
        await update.message.reply_text("📭 Меню пусто")
        session.close()
        return
    
    # Группируем по категориям
    categories = session.query(Category).all()
    
    message = "📋 *Текущее меню:*\n\n"
    
    for category in categories:
        category_items = [item for item in items if item.category_id == category.id]
        if category_items:
            message += f"*{category.display_name}:*\n"
            for item in category_items:
                nutrition = session.query(NutritionalInfo).filter_by(menu_item_id=item.id).first()
                nutrition_text = f" ({nutrition.calories} ккал)" if nutrition else ""
                message += f"• {item.id}. {item.name} - {item.price}₽{nutrition_text}\n"
            message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    session.close()

# ===================== УДАЛЕНИЕ БЛЮДА =====================

async def delete_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать удаление блюда"""
    if not context.user_data.get('admin_mode'):
        return
    
    session = Session()
    items = session.query(MenuItem).filter_by(is_available=True).all()
    
    if not items:
        await update.message.reply_text("📭 Нет блюд для удаления")
        session.close()
        return
    
    items_text = "🗑 *Выберите блюдо для удаления (введите номер):*\n\n"
    for item in items:
        items_text += f"{item.id}. {item.name}\n"
    
    context.user_data['delete_state'] = DELETE_SELECT
    context.user_data['in_delete_mode'] = True
    await update.message.reply_text(items_text, parse_mode='Markdown')
    session.close()

async def delete_item_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления"""
    # Проверяем, что мы действительно в режиме удаления
    if context.user_data.get('delete_state') != DELETE_SELECT:
        return
    
    try:
        item_id = int(update.message.text)
        session = Session()
        item = session.query(MenuItem).get(item_id)
        
        if not item:
            await update.message.reply_text("❌ Блюдо не найдено. Попробуйте снова:")
            session.close()
            return
        
        # Вместо удаления помечаем как недоступное
        item.is_available = False
        session.commit()
        session.close()
        
        # Очищаем состояние удаления
        context.user_data.pop('delete_state', None)
        context.user_data.pop('in_delete_mode', None)
        
        await update.message.reply_text(
            f"✅ Блюдо '{item.name}' удалено из меню",
            reply_markup=get_admin_keyboard()
        )
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректный номер")

# ===================== РЕДАКТИРОВАНИЕ БЛЮДА =====================

async def edit_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать редактирование блюда"""
    if not context.user_data.get('admin_mode'):
        return
    
    session = Session()
    items = session.query(MenuItem).filter_by(is_available=True).all()
    session.close()
    
    if not items:
        await update.message.reply_text("📭 Нет доступных блюд для редактирования")
        return
    
    items_text = "✏️ *Выберите блюдо для редактирования (введите номер):*\n\n"
    for item in items:
        items_text += f"{item.id}. {item.name}\n"
    
    context.user_data['edit_state'] = EDIT_SELECT
    context.user_data['in_edit_mode'] = True
    await update.message.reply_text(items_text, parse_mode='Markdown')

async def edit_item_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор блюда для редактирования"""
    # Проверяем, что мы действительно в режиме выбора блюда для редактирования
    if context.user_data.get('edit_state') != EDIT_SELECT:
        return
    
    try:
        item_id = int(update.message.text)
        session = Session()
        item = session.query(MenuItem).get(item_id)
        
        if not item:
            await update.message.reply_text("❌ Блюдо не найдено. Попробуйте снова:")
            session.close()
            return
        
        context.user_data['editing_item_id'] = item_id
        
        # Показываем текущую информацию
        nutrition = session.query(NutritionalInfo).filter_by(menu_item_id=item_id).first()
        
        message = f"*Редактирование: {item.name}*\n\n"
        message += f"1. Название: {item.name}\n"
        message += f"2. Состав: {item.composition}\n"
        message += f"3. Цена: {item.price}₽\n"
        message += f"4. Категория: {item.category.display_name}\n"
        message += f"5. Фото: {'✅ есть' if item.photo_file_id else '❌ нет'}\n"
        
        if nutrition:
            message += f"6. КБЖУ: {nutrition.weight}г, {nutrition.calories}ккал, б{nutrition.proteins}/ж{nutrition.fats}/у{nutrition.carbs}\n"
        else:
            message += "6. КБЖУ: не указано\n"
        
        message += f"7. Рекомендации: {'✅ есть' if item.drink_recommendations else '❌ нет'}\n\n"
        message += "Введите номер поля для редактирования (1-7):"
        
        context.user_data['edit_state'] = EDIT_FIELD
        await update.message.reply_text(message, parse_mode='Markdown')
        session.close()
        
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректный номер")

async def edit_item_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор поля для редактирования"""
    # Проверяем, что мы действительно в режиме выбора поля
    if context.user_data.get('edit_state') != EDIT_FIELD:
        return
    
    try:
        field_num = int(update.message.text)
        if field_num < 1 or field_num > 7:
            await update.message.reply_text("❌ Пожалуйста, введите номер от 1 до 7")
            return
        
        context.user_data['edit_field'] = field_num
        context.user_data['edit_state'] = EDIT_VALUE
        
        prompts = {
            1: "📝 Введите новое название:",
            2: "📋 Введите новый состав:",
            3: "💰 Введите новую цену:",
            4: "📁 Введите новый номер категории (1-3):",
            5: "📸 Отправьте новое фото или 'удалить' чтобы убрать фото:",
            6: "📊 Введите новые данные КБЖУ в формате: вес,калории,белки,жиры,углеводы\nИли 'удалить' чтобы убрать КБЖУ:",
            7: "🍷 Введите новые рекомендации по напиткам (каждая с новой строки в формате Название: описание) или 'удалить':"
        }
        
        await update.message.reply_text(prompts[field_num])
        
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректный номер")

async def edit_item_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновление значения поля"""
    # Проверяем, что мы действительно в режиме ввода нового значения
    if context.user_data.get('edit_state') != EDIT_VALUE:
        return
    
    field_num = context.user_data.get('edit_field')
    item_id = context.user_data.get('editing_item_id')
    
    if not item_id or not field_num:
        await update.message.reply_text("❌ Ошибка: данные редактирования потеряны. Начните заново.")
        context.user_data.pop('edit_state', None)
        context.user_data.pop('in_edit_mode', None)
        return
    
    session = Session()
    item = session.query(MenuItem).get(item_id)
    
    if not item:
        await update.message.reply_text("❌ Блюдо не найдено")
        session.close()
        context.user_data.pop('edit_state', None)
        context.user_data.pop('in_edit_mode', None)
        return
    
    success_message = ""
    
    if field_num == 1:
        item.name = update.message.text
        success_message = f"✅ Название изменено на: {update.message.text}"
        
    elif field_num == 2:
        item.composition = update.message.text
        success_message = f"✅ Состав изменен"
        
    elif field_num == 3:
        try:
            item.price = float(update.message.text)
            success_message = f"✅ Цена изменена на: {update.message.text}₽"
        except:
            await update.message.reply_text("❌ Неверный формат цены")
            session.close()
            return
            
    elif field_num == 4:
        try:
            category_id = int(update.message.text)
            category = session.query(Category).get(category_id)
            if category:
                item.category_id = category_id
                success_message = f"✅ Категория изменена на: {category.display_name}"
            else:
                await update.message.reply_text("❌ Категория не найдена")
                session.close()
                return
        except:
            await update.message.reply_text("❌ Неверный номер категории")
            session.close()
            return
            
    elif field_num == 5:
        if update.message.text and update.message.text.lower() == 'удалить':
            item.photo_file_id = None
            success_message = "✅ Фото удалено"
        elif update.message.photo:
            item.photo_file_id = update.message.photo[-1].file_id
            success_message = "✅ Фото обновлено"
        else:
            await update.message.reply_text("❌ Пожалуйста, отправьте фото или напишите 'удалить'")
            session.close()
            return
            
    elif field_num == 6:
        nutrition = session.query(NutritionalInfo).filter_by(menu_item_id=item_id).first()
        
        if update.message.text.lower() == 'удалить':
            if nutrition:
                session.delete(nutrition)
                success_message = "✅ КБЖУ удалено"
            else:
                success_message = "✅ КБЖУ и так не было"
        else:
            try:
                parts = update.message.text.split(',')
                if len(parts) != 5:
                    raise ValueError("Нужно 5 значений")
                
                weight, calories, proteins, fats, carbs = map(float, parts)
                
                if nutrition:
                    nutrition.weight = weight
                    nutrition.calories = calories
                    nutrition.proteins = proteins
                    nutrition.fats = fats
                    nutrition.carbs = carbs
                else:
                    new_nutrition = NutritionalInfo(
                        menu_item_id=item_id,
                        weight=weight,
                        calories=calories,
                        proteins=proteins,
                        fats=fats,
                        carbs=carbs
                    )
                    session.add(new_nutrition)
                
                success_message = f"✅ КБЖУ обновлено: {weight}г, {calories}ккал"
            except:
                await update.message.reply_text(
                    "❌ Неверный формат. Используйте: вес,калории,белки,жиры,углеводы\n"
                    "Например: 250,350,15,12,40"
                )
                session.close()
                return
                
    elif field_num == 7:
        if update.message.text.lower() == 'удалить':
            item.drink_recommendations = None
            success_message = "✅ Рекомендации удалены"
        else:
            recommendations = []
            lines = update.message.text.split('\n')
            for line in lines:
                if ':' in line:
                    name, desc = line.split(':', 1)
                    recommendations.append({
                        'name': name.strip(),
                        'description': desc.strip()
                    })
            item.drink_recommendations = json.dumps(recommendations, ensure_ascii=False)
            success_message = f"✅ {len(recommendations)} рекомендаций сохранено"
    
    session.commit()
    session.close()
    
    # Очищаем состояние редактирования
    context.user_data.pop('edit_state', None)
    context.user_data.pop('edit_field', None)
    context.user_data.pop('editing_item_id', None)
    context.user_data.pop('in_edit_mode', None)
    
    await update.message.reply_text(
        f"{success_message}\n\n✅ Редактирование завершено!",
        reply_markup=get_admin_keyboard()
    )

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    # Очищаем все состояния
    context.user_data.pop('add_state', None)
    context.user_data.pop('new_item', None)
    context.user_data.pop('in_add_mode', None)
    context.user_data.pop('edit_state', None)
    context.user_data.pop('edit_field', None)
    context.user_data.pop('editing_item_id', None)
    context.user_data.pop('in_edit_mode', None)
    context.user_data.pop('delete_state', None)
    context.user_data.pop('in_delete_mode', None)
    context.user_data.pop('admin_mode', None)
    context.user_data.pop('in_admin_panel', None)
    context.user_data.pop('search_mode', None)
    context.user_data.pop('search_results', None)
    
    await start_command(update, context)