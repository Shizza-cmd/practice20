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
from app.models import User, Category, Manufacturer, Supplier, Product, Order, PickupPoint
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
    
    # Создание пунктов выдачи
    pickup_points_data = [
        "420151, г. Лесной, ул. Вишневая, 32",
        "125061, г. Лесной, ул. Подгорная, 8",
        "630370, г. Лесной, ул. Шоссейная, 24",
        "400562, г. Лесной, ул. Зеленая, 32",
        "614510, г. Лесной, ул. Маяковского, 47",
        "410542, г. Лесной, ул. Светлая, 46",
        "620839, г. Лесной, ул. Цветочная, 8",
        "443890, г. Лесной, ул. Коммунистическая, 1",
        "603379, г. Лесной, ул. Спортивная, 46",
        "603721, г. Лесной, ул. Гоголя, 41",
        "410172, г. Лесной, ул. Северная, 13",
        "614611, г. Лесной, ул. Молодежная, 50",
        "454311, г.Лесной, ул. Новая, 19",
        "660007, г.Лесной, ул. Октябрьская, 19",
        "603036, г. Лесной, ул. Садовая, 4",
        "394060, г.Лесной, ул. Фрунзе, 43",
        "410661, г. Лесной, ул. Школьная, 50",
        "625590, г. Лесной, ул. Коммунистическая, 20",
        "625683, г. Лесной, ул. 8 Марта",
        "450983, г.Лесной, ул. Комсомольская, 26",
        "394782, г. Лесной, ул. Чехова, 3",
        "603002, г. Лесной, ул. Дзержинского, 28",
        "450558, г. Лесной, ул. Набережная, 30",
        "344288, г. Лесной, ул. Чехова, 1",
        "614164, г.Лесной,  ул. Степная, 30",
        "394242, г. Лесной, ул. Коммунистическая, 43",
        "660540, г. Лесной, ул. Солнечная, 25",
        "125837, г. Лесной, ул. Шоссейная, 40",
        "125703, г. Лесной, ул. Партизанская, 49",
        "625283, г. Лесной, ул. Победы, 46",
        "614753, г. Лесной, ул. Полевая, 35",
        "426030, г. Лесной, ул. Маяковского, 44",
        "450375, г. Лесной ул. Клубная, 44",
        "625560, г. Лесной, ул. Некрасова, 12",
        "630201, г. Лесной, ул. Комсомольская, 17",
        "190949, г. Лесной, ул. Мичурина, 26",
    ]
    
    for address in pickup_points_data:
        existing_pp = db.query(PickupPoint).filter(PickupPoint.address == address).first()
        if not existing_pp:
            pickup_point = PickupPoint(address=address)
            db.add(pickup_point)
    
    db.commit()
    print("База данных успешно инициализирована!")
    
except Exception as e:
    db.rollback()
    print(f"Ошибка при инициализации БД: {e}")
finally:
    db.close()

