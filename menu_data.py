from database import Session, Category, MenuItem, NutritionalInfo
import json

def init_categories():
    """Инициализация категорий"""
    session = Session()
    
    categories = [
        {'name': 'breakfast', 'display_name': '☀️ Завтраки'},
        {'name': 'main', 'display_name': '🍽 Основное меню'},
        {'name': 'bar', 'display_name': '🍷 Бар'}
    ]
    
    for cat_data in categories:
        category = session.query(Category).filter_by(name=cat_data['name']).first()
        if not category:
            category = Category(**cat_data)
            session.add(category)
    
    session.commit()
    print("✅ Категории созданы")

def add_sample_data():
    """Добавление примерных данных"""
    session = Session()
    
    # Получаем категории
    breakfast_cat = session.query(Category).filter_by(name='breakfast').first()
    main_cat = session.query(Category).filter_by(name='main').first()
    bar_cat = session.query(Category).filter_by(name='bar').first()
    
    # Пример блюда для завтраков
    if breakfast_cat:
        # Проверяем, есть ли уже такое блюдо
        existing = session.query(MenuItem).filter_by(name="Яичница с беконом").first()
        if not existing:
            eggs = MenuItem(
                name="🍳 Яичница с беконом",
                description="Классический завтрак",
                composition="Яйца (2 шт), бекон, тост, помидоры черри, зелень",
                price=450,
                category_id=breakfast_cat.id,
                photo_file_id=None,
                drink_recommendations=json.dumps([
                    {"name": "Апельсиновый фреш", "description": "Свежевыжатый апельсиновый сок"},
                    {"name": "Капучино", "description": "Классический кофе с молочной пенкой"}
                ], ensure_ascii=False),
                is_available=True
            )
            session.add(eggs)
            session.flush()
            
            nutrition = NutritionalInfo(
                menu_item_id=eggs.id,
                weight=250,
                calories=450,
                proteins=22,
                fats=28,
                carbs=15
            )
            session.add(nutrition)
            print("✅ Добавлен завтрак: Яичница с беконом")
    
    # Пример для основного меню
    if main_cat:
        existing = session.query(MenuItem).filter_by(name="Паста карбонара").first()
        if not existing:
            pasta = MenuItem(
                name="🍝 Паста карбонара",
                description="Итальянская паста",
                composition="Спагетти, бекон, яйцо, сыр пармезан, сливки, чеснок",
                price=650,
                category_id=main_cat.id,
                photo_file_id=None,
                drink_recommendations=json.dumps([
                    {"name": "Кьянти", "description": "Итальянское красное сухое вино"},
                    {"name": "Лимонад", "description": "Домашний лимонад с мятой"}
                ], ensure_ascii=False),
                is_available=True
            )
            session.add(pasta)
            session.flush()
            
            nutrition = NutritionalInfo(
                menu_item_id=pasta.id,
                weight=320,
                calories=580,
                proteins=18,
                fats=22,
                carbs=65
            )
            session.add(nutrition)
            print("✅ Добавлено основное блюдо: Паста карбонара")
    
    # Пример для бара
    if bar_cat:
        existing = session.query(MenuItem).filter_by(name="Мохито").first()
        if not existing:
            cocktail = MenuItem(
                name="🍹 Мохито",
                description="Освежающий коктейль",
                composition="Белый ром, лайм, мята, сахарный сироп, содовая, лед",
                price=550,
                category_id=bar_cat.id,
                photo_file_id=None,
                drink_recommendations=json.dumps([
                    {"name": "Закуска", "description": "Оливки и сыр"}
                ], ensure_ascii=False),
                is_available=True
            )
            session.add(cocktail)
            session.flush()
            
            nutrition = NutritionalInfo(
                menu_item_id=cocktail.id,
                weight=300,
                calories=220,
                proteins=0,
                fats=0,
                carbs=18
            )
            session.add(nutrition)
            print("✅ Добавлен напиток: Мохито")
    
    session.commit()
    session.close()
    print("✅ Примерные данные добавлены")

if __name__ == '__main__':
    print("🔄 Инициализация базы данных...")
    init_categories()
    add_sample_data()
    print("🎉 База данных успешно создана!")