from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    """Схема для входа"""
    login: str
    password: str


class UserResponse(BaseModel):
    """Схема ответа пользователя"""
    id: int
    login: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    """Базовая схема категории"""
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    """Схема ответа категории"""
    id: int

    class Config:
        from_attributes = True


class ManufacturerBase(BaseModel):
    """Базовая схема производителя"""
    name: str


class ManufacturerResponse(ManufacturerBase):
    """Схема ответа производителя"""
    id: int

    class Config:
        from_attributes = True


class SupplierBase(BaseModel):
    """Базовая схема поставщика"""
    name: str


class SupplierResponse(SupplierBase):
    """Схема ответа поставщика"""
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Базовая схема товара"""
    name: str
    category_id: int
    description: Optional[str] = None
    manufacturer_id: int
    supplier_id: int
    price: float = Field(..., ge=0)
    unit: str
    stock_quantity: int = Field(..., ge=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)


class ProductCreate(ProductBase):
    """Схема создания товара"""
    pass


class ProductUpdate(ProductBase):
    """Схема обновления товара"""
    name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    manufacturer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    price: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)


class ProductResponse(ProductBase):
    """Схема ответа товара"""
    id: int
    image_path: Optional[str] = None
    category: CategoryResponse
    manufacturer: ManufacturerResponse
    supplier: SupplierResponse
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    """Базовая схема позиции заказа"""
    product_id: int
    quantity: int = Field(..., gt=0)
    price: float = Field(..., ge=0)


class OrderItemResponse(OrderItemBase):
    """Схема ответа позиции заказа"""
    id: int
    order_id: int
    product: ProductResponse

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Базовая схема заказа"""
    article: str
    status: str
    pickup_address: str
    order_date: datetime
    delivery_date: Optional[datetime] = None


class OrderCreate(OrderBase):
    """Схема создания заказа"""
    items: list[OrderItemBase] = []


class OrderUpdate(BaseModel):
    """Схема обновления заказа"""
    article: Optional[str] = None
    status: Optional[str] = None
    pickup_address: Optional[str] = None
    order_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None


class OrderResponse(OrderBase):
    """Схема ответа заказа"""
    id: int
    items: list[OrderItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

