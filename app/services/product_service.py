from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models import Product, Category, Manufacturer, Supplier, PickupPoint
from app.schemas import ProductCreate, ProductUpdate
from typing import Optional


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    supplier_id: Optional[int] = None,
    sort_by_stock: Optional[str] = None
):
    """Получение списка товаров с фильтрацией, поиском и сортировкой"""
    # Используем outerjoin для случаев, когда связанные данные могут отсутствовать
    query = db.query(Product).outerjoin(Category).outerjoin(Manufacturer).outerjoin(Supplier)

    # Поиск по текстовым полям
    if search:
        search_filter = or_(
            Product.name.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%"),
            Category.name.ilike(f"%{search}%"),
            Manufacturer.name.ilike(f"%{search}%"),
            Supplier.name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Фильтрация по поставщику
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)

    # Сортировка по количеству на складе
    if sort_by_stock == "asc":
        query = query.order_by(Product.stock_quantity.asc())
    elif sort_by_stock == "desc":
        query = query.order_by(Product.stock_quantity.desc())

    return query.offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int) -> Product | None:
    """Получение товара по ID"""
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, product: ProductCreate, image_path: Optional[str] = None) -> Product:
    """Создание нового товара"""
    db_product = Product(**product.dict(), image_path=image_path)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(
    db: Session,
    product_id: int,
    product: ProductUpdate,
    image_path: Optional[str] = None
) -> Product:
    """Обновление товара"""
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    update_data = product.dict(exclude_unset=True)
    if image_path:
        update_data["image_path"] = image_path

    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    """Удаление товара"""
    db_product = get_product(db, product_id)
    if not db_product:
        return False

    # Проверка наличия товара в заказах
    if db_product.order_items:
        return False

    db.delete(db_product)
    db.commit()
    return True


def get_categories(db: Session):
    """Получение всех категорий"""
    return db.query(Category).all()


def get_manufacturers(db: Session):
    """Получение всех производителей"""
    return db.query(Manufacturer).all()


def get_suppliers(db: Session):
    """Получение всех поставщиков"""
    return db.query(Supplier).all()


def get_pickup_points(db: Session):
    """Получение всех пунктов выдачи"""
    return db.query(PickupPoint).all()


def get_product_by_article(db: Session, article: str) -> Product | None:
    """Получение товара по артикулу"""
    return db.query(Product).filter(Product.article == article).first()

