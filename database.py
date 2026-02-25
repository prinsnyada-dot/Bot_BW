from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    display_name = Column(String(100))
    items = relationship('MenuItem', back_populates='category')

class NutritionalInfo(Base):
    __tablename__ = 'nutritional_info'
    
    id = Column(Integer, primary_key=True)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), unique=True)
    weight = Column(Float)      # Вес порции (г)
    calories = Column(Float)    # Калории (ккал)
    proteins = Column(Float)    # Белки (г)
    fats = Column(Float)        # Жиры (г)
    carbs = Column(Float)       # Углеводы (г)
    
    menu_item = relationship('MenuItem', back_populates='nutritional_info')

class MenuItem(Base):
    __tablename__ = 'menu_items'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    description = Column(Text, default='')  # Добавлено поле description
    composition = Column(Text)
    price = Column(Float)
    category_id = Column(Integer, ForeignKey('categories.id'))
    is_available = Column(Boolean, default=True)
    drink_recommendations = Column(Text)  # JSON строка с рекомендациями
    photo_file_id = Column(String(200))   # Telegram file_id для фото
    
    category = relationship('Category', back_populates='items')
    nutritional_info = relationship('NutritionalInfo', uselist=False, back_populates='menu_item')

# Создаем базу данных
engine = create_engine('sqlite:///restaurant_menu.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

print("✅ База данных настроена")