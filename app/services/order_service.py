from sqlalchemy.orm import Session
from app.models import Order, OrderItem
from app.schemas import OrderCreate, OrderUpdate
from typing import Optional


def get_orders(db: Session, skip: int = 0, limit: int = 100):
    """Получение списка заказов"""
    return db.query(Order).offset(skip).limit(limit).all()


def get_order(db: Session, order_id: int) -> Order | None:
    """Получение заказа по ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def create_order(db: Session, order: OrderCreate) -> Order:
    """Создание нового заказа"""
    db_order = Order(
        article=order.article,
        status=order.status,
        pickup_address=order.pickup_address,
        order_date=order.order_date,
        delivery_date=order.delivery_date
    )
    db.add(db_order)
    db.flush()

    # Добавление позиций заказа
    for item in order.items:
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_order)
    return db_order


def update_order(db: Session, order_id: int, order: OrderUpdate) -> Order:
    """Обновление заказа"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    update_data = order.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)

    db.commit()
    db.refresh(db_order)
    return db_order


def delete_order(db: Session, order_id: int) -> bool:
    """Удаление заказа"""
    db_order = get_order(db, order_id)
    if not db_order:
        return False

    db.delete(db_order)
    db.commit()
    return True

