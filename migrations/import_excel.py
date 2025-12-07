"""
Скрипт импорта данных из Excel файлов
Импортирует данные из файлов в папке pril
"""
import sys
import os

# Добавление корневой директории проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Category, Manufacturer, Supplier, Product, Order
from app.services.auth_service import get_password_hash
from datetime import datetime

db = SessionLocal()

def import_users_from_excel(filepath: str):
    """Импорт пользователей из Excel файла"""
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден")
        return
    
    try:
        df = pd.read_excel(filepath)
        print(f"Найдено {len(df)} записей пользователей")
        
        for _, row in df.iterrows():
            try:
                login = str(row.get('Логин', '')).strip()
                password = str(row.get('Пароль', '')).strip()
                full_name = str(row.get('ФИО', '')).strip()
                role = str(row.get('Роль', 'client')).strip().lower()
                
                if not login or not password:
                    continue
                
                existing_user = db.query(User).filter(User.login == login).first()
                if not existing_user:
                    user = User(
                        login=login,
                        password_hash=get_password_hash(password),
                        full_name=full_name,
                        role=role
                    )
                    db.add(user)
                    print(f"Добавлен пользователь: {login}")
            except Exception as e:
                print(f"Ошибка при импорте пользователя: {e}")
                continue
        
        db.commit()
        print("Пользователи успешно импортированы")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при импорте пользователей: {e}")


def import_products_from_excel(filepath: str):
    """Импорт товаров из Excel файла"""
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден")
        return
    
    try:
        df = pd.read_excel(filepath)
        print(f"Найдено {len(df)} записей товаров")
        
        for _, row in df.iterrows():
            try:
                # Получение или создание категории
                category_name = str(row.get('Категория', '')).strip()
                if not category_name:
                    continue
                category = db.query(Category).filter(Category.name == category_name).first()
                if not category:
                    category = Category(name=category_name)
                    db.add(category)
                    db.flush()
                
                # Получение или создание производителя
                manufacturer_name = str(row.get('Производитель', '')).strip()
                if not manufacturer_name:
                    continue
                manufacturer = db.query(Manufacturer).filter(Manufacturer.name == manufacturer_name).first()
                if not manufacturer:
                    manufacturer = Manufacturer(name=manufacturer_name)
                    db.add(manufacturer)
                    db.flush()
                
                # Получение или создание поставщика
                supplier_name = str(row.get('Поставщик', '')).strip()
                if not supplier_name:
                    continue
                supplier = db.query(Supplier).filter(Supplier.name == supplier_name).first()
                if not supplier:
                    supplier = Supplier(name=supplier_name)
                    db.add(supplier)
                    db.flush()
                
                # Создание товара
                product = Product(
                    name=str(row.get('Наименование', '')).strip(),
                    category_id=category.id,
                    description=str(row.get('Описание', '')).strip(),
                    manufacturer_id=manufacturer.id,
                    supplier_id=supplier.id,
                    price=float(row.get('Цена', 0)),
                    unit=str(row.get('Единица измерения', 'шт')).strip(),
                    stock_quantity=int(row.get('Количество на складе', 0)),
                    discount_percent=float(row.get('Скидка', 0))
                )
                
                # Обработка изображения
                image_num = str(row.get('Фото', '')).strip()
                if image_num and image_num.isdigit():
                    image_path = f"static/images/products/{image_num}.jpg"
                    if os.path.exists(f"pril/{image_num}.jpg"):
                        # Копируем изображение
                        import shutil
                        os.makedirs("app/static/images/products", exist_ok=True)
                        shutil.copy(f"pril/{image_num}.jpg", f"app/{image_path}")
                    product.image_path = image_path
                
                db.add(product)
                print(f"Добавлен товар: {product.name}")
                
            except Exception as e:
                print(f"Ошибка при импорте товара: {e}")
                continue
        
        db.commit()
        print("Товары успешно импортированы")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при импорте товаров: {e}")


def import_orders_from_excel(filepath: str):
    """Импорт заказов из Excel файла"""
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден")
        return
    
    try:
        df = pd.read_excel(filepath)
        print(f"Найдено {len(df)} записей заказов")
        
        for _, row in df.iterrows():
            try:
                article = str(row.get('Артикул', '')).strip()
                status = str(row.get('Статус', 'новый')).strip()
                pickup_address = str(row.get('Адрес пункта выдачи', '')).strip()
                
                # Обработка даты заказа
                order_date_str = row.get('Дата заказа', '')
                if pd.isna(order_date_str):
                    order_date = datetime.now()
                elif isinstance(order_date_str, str):
                    try:
                        order_date = datetime.strptime(order_date_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        order_date = datetime.now()
                else:
                    order_date = order_date_str if isinstance(order_date_str, datetime) else datetime.now()
                
                # Обработка даты доставки
                delivery_date_str = row.get('Дата доставки', '')
                delivery_date = None
                if not pd.isna(delivery_date_str):
                    if isinstance(delivery_date_str, str):
                        try:
                            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    elif isinstance(delivery_date_str, datetime):
                        delivery_date = delivery_date_str
                
                if not article:
                    continue
                
                order = Order(
                    article=article,
                    status=status,
                    pickup_address=pickup_address,
                    order_date=order_date,
                    delivery_date=delivery_date
                )
                db.add(order)
                print(f"Добавлен заказ: {article}")
                
            except Exception as e:
                print(f"Ошибка при импорте заказа: {e}")
                continue
        
        db.commit()
        print("Заказы успешно импортированы")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при импорте заказов: {e}")


if __name__ == "__main__":
    pril_dir = "pril"
    
    # Импорт пользователей
    users_file = os.path.join(pril_dir, "user_import.xlsx")
    if os.path.exists(users_file):
        print("\n=== Импорт пользователей ===")
        import_users_from_excel(users_file)
    
    # Импорт товаров
    products_file = os.path.join(pril_dir, "Tovar.xlsx")
    if os.path.exists(products_file):
        print("\n=== Импорт товаров ===")
        import_products_from_excel(products_file)
    
    # Импорт заказов
    orders_file = os.path.join(pril_dir, "Заказ_import.xlsx")
    if os.path.exists(orders_file):
        print("\n=== Импорт заказов ===")
        import_orders_from_excel(orders_file)
    
    db.close()
    print("\nИмпорт завершен!")

