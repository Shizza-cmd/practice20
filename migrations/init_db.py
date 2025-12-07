"""
Скрипт инициализации базы данных
Создает все таблицы и заполняет начальными данными
"""
import sys
import os

# Добавление корневой директории проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import User, Category, Manufacturer, Supplier, Product, Order
from app.services.auth_service import get_password_hash
from datetime import datetime

# Создание всех таблиц
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Создание пользователей
    users_data = [
        {"login": "admin", "password": "admin123", "full_name": "Администратор Системы", "role": "admin"},
        {"login": "manager", "password": "manager123", "full_name": "Менеджер Иванов И.И.", "role": "manager"},
        {"login": "client", "password": "client123", "full_name": "Клиент Петров П.П.", "role": "client"},
    ]
    
    for user_data in users_data:
        existing_user = db.query(User).filter(User.login == user_data["login"]).first()
        if not existing_user:
            try:
                password_hash = get_password_hash(user_data["password"])
                user = User(
                    login=user_data["login"],
                    password_hash=password_hash,
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
                db.add(user)
            except Exception as e:
                print(f"Ошибка при создании пользователя {user_data['login']}: {e}")
                raise
    
    # Создание категорий
    categories_data = [
        "Кроссовки",
        "Ботинки",
        "Туфли",
        "Сапоги",
        "Тапочки",
        "Сандалии"
    ]
    
    for cat_name in categories_data:
        existing_cat = db.query(Category).filter(Category.name == cat_name).first()
        if not existing_cat:
            category = Category(name=cat_name)
            db.add(category)
    
    # Создание производителей
    manufacturers_data = [
        "Nike",
        "Adidas",
        "Puma",
        "Reebok",
        "New Balance",
        "Converse"
    ]
    
    for man_name in manufacturers_data:
        existing_man = db.query(Manufacturer).filter(Manufacturer.name == man_name).first()
        if not existing_man:
            manufacturer = Manufacturer(name=man_name)
            db.add(manufacturer)
    
    # Создание поставщиков
    suppliers_data = [
        "ООО Поставщик 1",
        "ООО Поставщик 2",
        "ИП Иванов",
        "ООО Обувь Торг"
    ]
    
    for sup_name in suppliers_data:
        existing_sup = db.query(Supplier).filter(Supplier.name == sup_name).first()
        if not existing_sup:
            supplier = Supplier(name=sup_name)
            db.add(supplier)
    
    db.commit()
    print("База данных успешно инициализирована!")
    
except Exception as e:
    db.rollback()
    print(f"Ошибка при инициализации БД: {e}")
finally:
    db.close()

