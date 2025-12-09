"""
Скрипт для пересоздания базы данных
"""
import os
from app.database import Base, engine
# ВАЖНО: Импортируем все модели, чтобы они были зарегистрированы в Base.metadata
from app.models import User, Category, Manufacturer, Supplier, Product, Order, OrderItem

# Удаляем старую БД если она есть
db_file = "shoe_store.db"
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Удалена старая база данных: {db_file}")

# Создаем новую БД со всеми таблицами
Base.metadata.create_all(bind=engine)
print("База данных успешно пересоздана!")
print(f"Созданы таблицы: {', '.join(Base.metadata.tables.keys())}")
print("\nВАЖНО: Артикулы заказов больше НЕ уникальны - разные люди могут заказывать одни и те же товары!")

