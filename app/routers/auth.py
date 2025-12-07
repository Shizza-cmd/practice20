from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import authenticate_user
from app.schemas import UserLogin, UserResponse
from app.models import User

router = APIRouter()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Получение текущего пользователя из сессии"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_role(allowed_roles: list[str]):
    """Декоратор для проверки роли пользователя"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or args[0] if args else None
            db = kwargs.get("db") or args[1] if len(args) > 1 else None
            
            if not request:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
            
            user = get_current_user(request, db)
            if not user or user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав доступа"
                )
            kwargs["current_user"] = user
            return await func(*args, **kwargs)
        return wrapper
    return decorator


@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db),
    login: str = Form(...),
    password: str = Form(...)
):
    """Авторизация пользователя"""
    try:
        user = authenticate_user(db, login, password)
        request.session["user_id"] = user.id
        request.session["user_role"] = user.role
        return RedirectResponse(url="/products/", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="app/templates")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": e.detail
        })
    except Exception as e:
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="app/templates")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Ошибка авторизации: {str(e)}"
        })


@router.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    if not current_user:
        return None
    return UserResponse.model_validate(current_user)

