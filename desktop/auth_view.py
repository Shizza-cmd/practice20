"""
Модуль авторизации для десктопного приложения
"""
import flet as ft
from app.database import SessionLocal
from app.services.auth_service import verify_password, get_user_by_login
from desktop.notifications import show_error, show_warning, show_info


def create_login_view(page: ft.Page, app_state):
    """Создание экрана входа"""
    
    login_field = ft.TextField(
        label="Логин",
        width=300,
        autofocus=True,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color="#000000"
    )
    
    password_field = ft.TextField(
        label="Пароль",
        width=300,
        password=True,
        can_reveal_password=True,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color="#000000"
    )
    
    def on_login_click(e):
        """Обработчик входа"""
        login = login_field.value
        password = password_field.value
        
        if not login or not password:
            show_warning(page, "Введите логин и пароль", "Внимание")
            return
        
        try:
            db = SessionLocal()
            try:
                user = get_user_by_login(db, login)
                if not user:
                    raise ValueError("Неверный логин или пароль")
                if not verify_password(password, user.password_hash):
                    raise ValueError("Неверный логин или пароль")
                
                app_state.set_user(user)
                
                from desktop.products_view import create_products_view
                page.views.clear()
                page.views.append(create_products_view(page, app_state))
                page.update()
            finally:
                db.close()
            
        except Exception as ex:
            show_error(page, str(ex))
    
    def on_guest_click(e):
        """Обработчик просмотра как гость"""
        from app.models import User
        guest_user = User(
            id=0,
            login="guest",
            password_hash="",
            full_name="Гость",
            role="guest"
        )
        app_state.set_user(guest_user)
        
        from desktop.products_view import create_products_view
        page.views.clear()
        page.views.append(create_products_view(page, app_state))
        page.update()
    
    login_button = ft.ElevatedButton(
        text="Войти",
        on_click=on_login_click,
        width=300,
        bgcolor="#00FA9A",
        color="#000000",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=5),
            side=ft.BorderSide(2, "#000000")
        )
    )
    
    guest_button = ft.ElevatedButton(
        text="Просмотр как гость",
        on_click=on_guest_click,
        width=300,
        bgcolor="#00FA9A",
        color="#000000",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=5),
            side=ft.BorderSide(2, "#000000")
        )
    )
    
    # Обработка Enter
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Enter":
            on_login_click(e)
    
    page.on_keyboard_event = on_keyboard
    
    # Заголовок с зеленым фоном
    header = ft.Container(
        content=ft.Text(
            "ООО Обувь",
            size=24,
            weight=ft.FontWeight.BOLD,
            color="#000000",
            font_family="Times New Roman",
            text_align=ft.TextAlign.CENTER
        ),
        bgcolor="#00FF00",
        padding=15,
        width=350,
        alignment=ft.alignment.center,
        border=ft.border.all(2, "#000000")
    )
    
    view = ft.View(
        route="/",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        header,
                        ft.Container(height=20),
                        ft.Image(
                            src="app/static/images/Icon.png",
                            width=100,
                            height=100,
                            error_content=ft.Icon(ft.Icons.SHOPPING_BAG, size=100, color="#00FA9A")
                        ),
                        ft.Text(
                            "Система управления продажей обуви",
                            size=14,
                            color="#000000",
                            font_family="Times New Roman"
                        ),
                        ft.Container(height=20),
                        login_field,
                        password_field,
                        ft.Container(height=10),
                        login_button,
                        guest_button
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor="#FFFFFF"
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor="#FFFFFF"
    )
    
    return view
