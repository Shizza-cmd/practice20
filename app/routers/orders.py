from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.services.order_service import get_orders, get_order, create_order, update_order, delete_order
from app.schemas import OrderCreate, OrderUpdate, OrderItemBase
from app.routers.auth import get_current_user
from app.models import User, Order

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def orders_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Список заказов"""
    if not current_user or current_user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")
    
    orders = get_orders(db)
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": orders,
        "current_user": current_user
    })


@router.get("/add", response_class=HTMLResponse)
async def order_add_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Форма добавления заказа"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("order_form.html", {
        "request": request,
        "current_user": current_user,
        "order": None,
        "statuses": ["новый", "в обработке", "выполнен", "отменен"]
    })


@router.get("/edit/{order_id}", response_class=HTMLResponse)
async def order_edit_form(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Форма редактирования заказа"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("order_form.html", {
        "request": request,
        "current_user": current_user,
        "order": order,
        "statuses": ["новый", "в обработке", "выполнен", "отменен"]
    })


@router.post("/create")
async def order_create(
    request: Request,
    db: Session = Depends(get_db),
    article: str = Form(...),
    status: str = Form(...),
    pickup_address: str = Form(...),
    order_date: str = Form(...),
    delivery_date: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Создание заказа"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    try:
        order_date_dt = datetime.fromisoformat(order_date.replace("T", " "))
        delivery_date_dt = datetime.fromisoformat(delivery_date.replace("T", " ")) if delivery_date else None
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный формат даты")
    
    order_data = OrderCreate(
        article=article,
        status=status,
        pickup_address=pickup_address,
        order_date=order_date_dt,
        delivery_date=delivery_date_dt
    )
    
    create_order(db, order_data)
    return RedirectResponse(url="/orders/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/update/{order_id}")
async def order_update(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    article: str = Form(...),
    status: str = Form(...),
    pickup_address: str = Form(...),
    order_date: str = Form(...),
    delivery_date: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Обновление заказа"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    
    try:
        order_date_dt = datetime.fromisoformat(order_date.replace("T", " "))
        delivery_date_dt = datetime.fromisoformat(delivery_date.replace("T", " ")) if delivery_date else None
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный формат даты")
    
    order_data = OrderUpdate(
        article=article,
        status=status,
        pickup_address=pickup_address,
        order_date=order_date_dt,
        delivery_date=delivery_date_dt
    )
    
    update_order(db, order_id, order_data)
    return RedirectResponse(url="/orders/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/delete/{order_id}")
async def order_delete(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление заказа"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    
    if delete_order(db, order_id):
        return RedirectResponse(url="/orders/", status_code=status.HTTP_303_SEE_OTHER)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

