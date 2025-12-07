from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
from app.database import engine, Base
from app.routers import auth, products, orders

# Создание таблиц БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ООО «Обувь»", description="Система управления продажей обуви")

# Подключение middleware для сессий
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])

# Инициализация шаблонов
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - окно входа"""
    # Проверка авторизации
    user_id = request.session.get("user_id")
    
    # Если пользователь авторизован, перенаправляем на список товаров
    if user_id:
        return RedirectResponse(url="/products/", status_code=303)
    
    return templates.TemplateResponse("login.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

