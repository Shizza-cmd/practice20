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
                # Обработка роли из поля "Роль сотрудника"
                role_str = str(row.get('Роль сотрудника', row.get('Роль', 'client'))).strip().lower()
                # Преобразование ролей
                if 'администратор' in role_str or 'admin' in role_str:
                    role = 'admin'
                elif 'менеджер' in role_str or 'manager' in role_str:
                    role = 'manager'
                else:
                    role = 'client'
                
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
        
        product_counter = 0  # Счётчик для генерации артикулов
        
        for _, row in df.iterrows():
            try:
                # Получение или создание категории
                # Используем поле "Категория товара" (Женская обувь, Мужская обувь)
                category_name = str(row.get('Категория товара', row.get('Категория', ''))).strip()
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
                
                # Обработка цены
                price_val = row.get('Цена', 0)
                try:
                    if pd.isna(price_val):
                        price_val = 0
                    else:
                        price_val = float(price_val)
                except:
                    price_val = 0
                
                # Обработка количества
                stock_val = row.get('Кол-во на складе', row.get('Количество на складе', 0))
                try:
                    if pd.isna(stock_val):
                        stock_val = 0
                    else:
                        stock_val = int(float(stock_val))  # Сначала float, потом int для обработки "0.0"
                except:
                    stock_val = 0
                
                # Обработка скидки
                discount_val = row.get('Действующая скидка', row.get('Скидка', 0))
                try:
                    if pd.isna(discount_val):
                        discount_val = 0
                    else:
                        discount_val = float(discount_val)
                except:
                    discount_val = 0
                
                # Получение артикула из Excel или генерация
                article_val = str(row.get('Артикул', row.get('Артикул товара', ''))).strip()
                if not article_val:
                    # Генерируем артикул если не указан
                    product_counter += 1
                    article_val = f"ART-{product_counter:04d}"
                
                # Проверка уникальности артикула
                existing_product = db.query(Product).filter(Product.article == article_val).first()
                if existing_product:
                    print(f"Товар с артикулом {article_val} уже существует, пропускаем")
                    continue
                
                # Создание товара
                product = Product(
                    article=article_val,
                    name=str(row.get('Наименование товара', row.get('Наименование', ''))).strip(),
                    category_id=category.id,
                    description=str(row.get('Описание товара', row.get('Описание', ''))).strip() or None,
                    manufacturer_id=manufacturer.id,
                    supplier_id=supplier.id,
                    price=price_val,
                    unit=str(row.get('Единица измерения', 'шт')).strip() or 'шт',
                    stock_quantity=stock_val,
                    discount_percent=discount_val
                )
                
                # Обработка изображения
                image_num = str(row.get('Фото', '')).strip()
                if image_num:
                    # Убираем расширение если есть
                    image_num = image_num.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
                    if image_num.isdigit():
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
    
    # Загружаем адреса пунктов выдачи
    pickup_points_file = os.path.join("pril", "Пункты выдачи_import.xlsx")
    pickup_points = []
    if os.path.exists(pickup_points_file):
        pickup_df = pd.read_excel(pickup_points_file)
        # Адреса в первой колонке, индекс соответствует номеру
        pickup_points = pickup_df.iloc[:, 0].tolist()
        print(f"Загружено {len(pickup_points)} пунктов выдачи")
    
    try:
        df = pd.read_excel(filepath)
        print(f"Найдено {len(df)} записей заказов")
        
        for _, row in df.iterrows():
            try:
                # Используем поле "Артикул заказа"
                article = str(row.get('Артикул заказа', '')).strip()
                status = str(row.get('Статус заказа', row.get('Статус', 'новый'))).strip().lower()
                # Преобразуем статус
                if 'завершен' in status or 'выполнен' in status:
                    status = 'завершен'
                elif 'новый' in status:
                    status = 'новый'
                elif 'обработке' in status:
                    status = 'в обработке'
                elif 'отменен' in status:
                    status = 'отменен'
                else:
                    status = 'новый'
                
                # Адрес пункта выдачи - может быть номером или полным адресом
                pickup_address_raw = str(row.get('Адрес пункта выдачи', '')).strip()
                # Если это число, получаем полный адрес из списка пунктов выдачи
                if pickup_address_raw.isdigit():
                    pickup_index = int(pickup_address_raw) - 1  # Нумерация с 1
                    if 0 <= pickup_index < len(pickup_points):
                        pickup_address = pickup_points[pickup_index]
                    else:
                        pickup_address = f"Пункт выдачи #{pickup_address_raw}"
                else:
                    pickup_address = pickup_address_raw
                
                # Обработка даты заказа
                order_date_str = row.get('Дата заказа', '')
                if pd.isna(order_date_str):
                    order_date = datetime.now()
                elif isinstance(order_date_str, str):
                    # Пробуем разные форматы дат
                    for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']:
                        try:
                            order_date = datetime.strptime(order_date_str, fmt)
                            break
                        except:
                            continue
                    else:
                        order_date = datetime.now()
                else:
                    order_date = order_date_str if isinstance(order_date_str, datetime) else datetime.now()
                
                # Обработка даты доставки
                delivery_date_str = row.get('Дата доставки', '')
                delivery_date = None
                if not pd.isna(delivery_date_str):
                    if isinstance(delivery_date_str, str):
                        # Пробуем разные форматы дат
                        for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']:
                            try:
                                delivery_date = datetime.strptime(delivery_date_str, fmt)
                                break
                            except:
                                continue
                    elif isinstance(delivery_date_str, datetime):
                        delivery_date = delivery_date_str
                
                code = str(row.get('Код для получения', '')).strip()
                # Генерируем код если не указан
                if not code:
                    import random
                    import string
                    code = ''.join(random.choices(string.digits, k=6))

                if not article:
                    continue

                # Артикул заказа не уникален - разные заказы могут содержать одинаковые товары
                order = Order(
                    article=article,
                    status=status,
                    pickup_address=pickup_address,
                    order_date=order_date,
                    delivery_date=delivery_date,
                    code=code
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

