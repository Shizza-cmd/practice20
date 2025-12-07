from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from PIL import Image
from app.database import get_db
from app.services.product_service import (
    get_products, get_product, create_product, update_product,
    delete_product, get_categories, get_manufacturers, get_suppliers
)
from app.schemas import ProductCreate, ProductUpdate
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter()

# Директория для сохранения изображений
UPLOAD_DIR = "app/static/images/products"
MAX_IMAGE_SIZE = (300, 200)


def ensure_upload_dir():
    """Создание директории для загрузки изображений"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_image(file: UploadFile, product_id: int) -> str:
    """Сохранение изображения товара"""
    ensure_upload_dir()
    
    # Получение расширения файла
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"product_{product_id}{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Сохранение файла
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Изменение размера изображения
    try:
        img = Image.open(filepath)
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        img.save(filepath)
    except Exception as e:
        print(f"Ошибка обработки изображения: {e}")
    
    return f"static/images/products/{filename}"


def delete_old_image(image_path: str):
    """Удаление старого изображения"""
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Ошибка удаления изображения: {e}")


@router.get("/", response_class=HTMLResponse)
async def products_list(
    request: Request,
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    supplier_id: Optional[str] = None,
    sort_by_stock: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Список товаров"""
    # Определение роли пользователя
    role = current_user.role if current_user else "guest"
    
    # Преобразование supplier_id в int если передан
    supplier_id_int = None
    if supplier_id and supplier_id.strip():
        try:
            supplier_id_int = int(supplier_id)
        except ValueError:
            supplier_id_int = None
    
    # Проверка прав доступа для фильтрации/поиска
    if role not in ["manager", "admin"]:
        search = None
        supplier_id_int = None
        sort_by_stock = None
    
    products = get_products(db, search=search, supplier_id=supplier_id_int, sort_by_stock=sort_by_stock)
    suppliers = get_suppliers(db) if role in ["manager", "admin"] else []
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products,
        "suppliers": suppliers,
        "current_user": current_user,
        "search": search or "",
        "selected_supplier_id": supplier_id_int,
        "sort_by_stock": sort_by_stock or ""
    })


@router.get("/add", response_class=HTMLResponse)
async def product_add_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Форма добавления товара"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    categories = get_categories(db)
    manufacturers = get_manufacturers(db)
    suppliers = get_suppliers(db)
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "current_user": current_user,
        "categories": categories,
        "manufacturers": manufacturers,
        "suppliers": suppliers,
        "product": None
    })


@router.get("/edit/{product_id}", response_class=HTMLResponse)
async def product_edit_form(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Форма редактирования товара"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    
    categories = get_categories(db)
    manufacturers = get_manufacturers(db)
    suppliers = get_suppliers(db)
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("product_form.html", {
        "request": request,
        "current_user": current_user,
        "categories": categories,
        "manufacturers": manufacturers,
        "suppliers": suppliers,
        "product": product
    })


@router.post("/create")
async def product_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(None),
    manufacturer_id: int = Form(...),
    supplier_id: int = Form(...),
    price: float = Form(...),
    unit: str = Form(...),
    stock_quantity: int = Form(...),
    discount_percent: float = Form(0.0),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Создание товара"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    # Получение следующего ID
    from app.models import Product as ProductModel
    last_product = db.query(ProductModel).order_by(ProductModel.id.desc()).first()
    next_id = (last_product.id + 1) if last_product else 1
    
    product_data = ProductCreate(
        name=name,
        category_id=category_id,
        description=description,
        manufacturer_id=manufacturer_id,
        supplier_id=supplier_id,
        price=price,
        unit=unit,
        stock_quantity=stock_quantity,
        discount_percent=discount_percent
    )
    
    image_path = None
    if image and image.filename:
        image_path = save_image(image, next_id)
    
    product = create_product(db, product_data, image_path)
    return RedirectResponse(url="/products/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/update/{product_id}")
async def product_update(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(None),
    manufacturer_id: int = Form(...),
    supplier_id: int = Form(...),
    price: float = Form(...),
    unit: str = Form(...),
    stock_quantity: int = Form(...),
    discount_percent: float = Form(0.0),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Обновление товара"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    
    product_data = ProductUpdate(
        name=name,
        category_id=category_id,
        description=description,
        manufacturer_id=manufacturer_id,
        supplier_id=supplier_id,
        price=price,
        unit=unit,
        stock_quantity=stock_quantity,
        discount_percent=discount_percent
    )
    
    image_path = None
    if image and image.filename:
        # Удаление старого изображения
        if product.image_path:
            delete_old_image(product.image_path)
        image_path = save_image(image, product_id)
    
    update_product(db, product_id, product_data, image_path)
    return RedirectResponse(url="/products/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/delete/{product_id}")
async def product_delete(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление товара"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    
    # Проверка наличия товара в заказах
    if product.order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно удалить товар, который присутствует в заказе"
        )
    
    # Удаление изображения
    if product.image_path:
        delete_old_image(product.image_path)
    
    if delete_product(db, product_id):
        return RedirectResponse(url="/products/", status_code=status.HTTP_303_SEE_OTHER)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка удаления товара")

