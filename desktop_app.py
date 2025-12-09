"""
Десктопное приложение ООО «Обувь»
"""
import flet as ft
from app.database import SessionLocal
from app.models import User
from desktop import auth_view, products_view, orders_view


class AppState:
    """Глобальное состояние приложения"""
    def __init__(self):
        self.current_user: User | None = None
        self.db = SessionLocal()
    
    def set_user(self, user: User):
        """Установка текущего пользователя"""
        self.current_user = user
    
    def logout(self):
        """Выход из системы"""
        self.current_user = None
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.db:
            self.db.close()


def main(page: ft.Page):
    """Главная функция приложения"""
    page.title = "ООО «Обувь» - Система управления продажей обуви"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 800
    page.window.min_height = 600
    page.theme = ft.Theme(font_family="Times New Roman")
    page.bgcolor = "#FFFFFF"  # Основной фон
    
    # Инициализация состояния
    app_state = AppState()
    page.data = app_state
    
    # Обработчик закрытия окна
    def on_window_event(e):
        if e.data == "close":
            app_state.close()
    
    page.window.on_event = on_window_event
    
    def navigate_to_login():
        """Переход на экран входа"""
        page.views.clear()
        page.views.append(auth_view.create_login_view(page, app_state))
        page.update()
    
    def navigate_to_products():
        """Переход на экран товаров"""
        if not app_state.current_user:
            navigate_to_login()
            return
        
        page.views.clear()
        page.views.append(products_view.create_products_view(page, app_state))
        page.update()
    
    def navigate_to_orders():
        """Переход на экран заказов"""
        if not app_state.current_user:
            navigate_to_login()
            return
        
        if app_state.current_user.role not in ["manager", "admin"]:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Доступ запрещен"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return
        
        page.views.clear()
        page.views.append(orders_view.create_orders_view(page, app_state))
        page.update()
    
    def on_view_pop(e):
        """Обработчик возврата назад"""
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = lambda e: None
    page.on_view_pop = on_view_pop
    
    # Начальный экран - вход
    navigate_to_login()


if __name__ == "__main__":
    ft.app(target=main)

