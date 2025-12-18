"""
Скрипт импорта данных из файлов
Импортирует данные из CSV файлов в папке resources/import_data
"""
import sys
import os

# Добавление корневой директории проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Category, Manufacturer, Supplier, Product
from datetime import datetime

db = SessionLocal()

def import_products_from_csv(filepath: str):
    """Импорт товаров из CSV файла"""
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Получение или создание категории
                category = db.query(Category).filter(Category.name == row['category']).first()
                if not category:
                    category = Category(name=row['category'])
                    db.add(category)
                    db.flush()
                
                # Получение или создание производителя
                manufacturer = db.query(Manufacturer).filter(Manufacturer.name == row['manufacturer']).first()
                if not manufacturer:
                    manufacturer = Manufacturer(name=row['manufacturer'])
                    db.add(manufacturer)
                    db.flush()
                
                # Получение или создание поставщика
                supplier = db.query(Supplier).filter(Supplier.name == row['supplier']).first()
                if not supplier:
                    supplier = Supplier(name=row['supplier'])
                    db.add(supplier)
                    db.flush()
                
                # Создание товара
                product = Product(
                    name=row['name'],
                    category_id=category.id,
                    description=row.get('description', ''),
                    manufacturer_id=manufacturer.id,
                    supplier_id=supplier.id,
                    price=float(row['price']),
                    unit=row.get('unit', 'шт'),
                    stock_quantity=int(row.get('stock_quantity', 0)),
                    discount_percent=float(row.get('discount_percent', 0))
                )
                db.add(product)
                
            except Exception as e:
                print(f"Ошибка при импорте строки: {e}")
                continue
    
    db.commit()
    print(f"Данные из {filepath} успешно импортированы")


def import_orders_from_csv(filepath: str):
    """Импорт заказов из CSV файла"""
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден")
        return
    
    from app.models import Order
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                order = Order(
                    article=row['article'],
                    status=row['status'],
                    pickup_address=row['pickup_address'],
                    order_date=datetime.strptime(row['order_date'], '%Y-%m-%d %H:%M:%S'),
                    delivery_date=datetime.strptime(row['delivery_date'], '%Y-%m-%d %H:%M:%S') if row.get('delivery_date') else None,
                    code=row['code']
                )
                db.add(order)
                
            except Exception as e:
                print(f"Ошибка при импорте строки: {e}")
                continue
    
    db.commit()
    print(f"Данные из {filepath} успешно импортированы")


if __name__ == "__main__":
    import_dir = "resources/import_data"
    
    # Импорт товаров
    products_file = os.path.join(import_dir, "products.csv")
    if os.path.exists(products_file):
        import_products_from_csv(products_file)
    
    # Импорт заказов
    orders_file = os.path.join(import_dir, "orders.csv")
    if os.path.exists(orders_file):
        import_orders_from_csv(orders_file)
    
    db.close()

