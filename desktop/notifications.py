"""Модуль уведомлений для десктопного приложения"""
import flet as ft


def show_error(page: ft.Page, message: str, title: str = "Ошибка"):
    """Показать ошибку (красный)"""
    _show_notification(page, title, message, "#F44336", ft.Icons.ERROR)


def show_warning(page: ft.Page, message: str, title: str = "Предупреждение"):
    """Показать предупреждение (оранжевый)"""
    _show_notification(page, title, message, "#FF9800", ft.Icons.WARNING)


def show_info(page: ft.Page, message: str, title: str = "Информация"):
    """Показать информацию (зелёный)"""
    _show_notification(page, title, message, "#4CAF50", ft.Icons.CHECK_CIRCLE)


def _show_notification(page: ft.Page, title: str, message: str, bgcolor: str, icon):
    """Внутренняя функция показа уведомления"""
    snack = ft.SnackBar(
        content=ft.Row([
            ft.Icon(icon, color="#FFFFFF", size=32),
            ft.Column([
                ft.Text(title, color="#FFFFFF", weight=ft.FontWeight.BOLD, size=18),
                ft.Text(message, color="#FFFFFF", size=16),
            ], spacing=2, tight=True),
        ], spacing=15),
        bgcolor=bgcolor,
        duration=4000,
        show_close_icon=True,
        close_icon_color="#FFFFFF"
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()

