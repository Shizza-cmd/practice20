from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)  # guest, client, manager, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Category(Base):
    """Модель категории товара"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    products = relationship("Product", back_populates="category")


class Manufacturer(Base):
    """Модель производителя"""
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)

    products = relationship("Product", back_populates="manufacturer")


class Supplier(Base):
    """Модель поставщика"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)

    products = relationship("Product", back_populates="supplier")


class Product(Base):
    """Модель товара"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(Text)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)  # единица измерения
    stock_quantity = Column(Integer, nullable=False, default=0)
    image_path = Column(String(500))
    discount_percent = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    manufacturer = relationship("Manufacturer", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    article = Column(String(100), nullable=False, index=True)  # Убрали unique=True - разные заказы могут содержать одинаковые товары
    status = Column(String(50), nullable=False)  # новый, в обработке, выполнен, отменен
    pickup_address = Column(Text, nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    delivery_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Модель позиции заказа"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # цена на момент заказа

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

