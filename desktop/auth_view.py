"""
Модуль авторизации для десктопного приложения
"""
import flet as ft
from app.database import SessionLocal
from app.services.auth_service import verify_password, get_user_by_login


def create_login_view(page: ft.Page, app_state):
    """Создание экрана входа"""
    
    login_field = ft.TextField(
        label="Логин",
        width=300,
        autofocus=True
    )
    
    password_field = ft.TextField(
        label="Пароль",
        width=300,
        password=True,
        can_reveal_password=True
    )
    
    error_text = ft.Text(
        value="",
        color=ft.Colors.RED,
        visible=False
    )
    
    def on_login_click(e):
        """Обработчик входа"""
        login = login_field.value
        password = password_field.value
        
        if not login or not password:
            error_text.value = "Введите логин и пароль"
            error_text.visible = True
            page.update()
            return
        
        try:
            db = SessionLocal()
            try:
                # Аутентификация без HTTPException
                user = get_user_by_login(db, login)
                if not user:
                    raise ValueError("Неверный логин или пароль")
                if not verify_password(password, user.password_hash):
                    raise ValueError("Неверный логин или пароль")
                
                app_state.set_user(user)
                
                # Переход на экран товаров
                from desktop.products_view import create_products_view
                page.views.clear()
                page.views.append(create_products_view(page, app_state))
                page.update()
            finally:
                db.close()
            
        except Exception as ex:
            error_text.value = str(ex)
            error_text.visible = True
            page.update()
    
    login_button = ft.ElevatedButton(
        text="Войти",
        on_click=on_login_click,
        width=300
    )
    
    # Обработка Enter
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Enter":
            on_login_click(e)
    
    page.on_keyboard_event = on_keyboard
    
    view = ft.View(
        route="/",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Image(
                            src="app/static/images/Icon.png",
                            width=100,
                            height=100,
                            error_content=ft.Icon(ft.Icons.SHOPPING_BAG, size=100)
                        ),
                        ft.Text(
                            "ООО «Обувь»",
                            size=32,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "Система управления продажей обуви",
                            size=16,
                            color=ft.Colors.GREY
                        ),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        login_field,
                        password_field,
                        error_text,
                        login_button
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    return view

