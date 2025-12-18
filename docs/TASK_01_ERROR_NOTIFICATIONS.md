# Задача 1: Уведомления об ошибках (предупреждение, ошибка, информация как всплывающие окна)

## Описание задачи
Заменить текстовые сообщения об ошибках на всплывающие диалоговые окна трёх типов:
- **Ошибка (Error)** — красный цвет, критические проблемы
- **Предупреждение (Warning)** — оранжевый цвет, некритичные проблемы
- **Информация (Info)** — синий/зелёный цвет, успешные операции

## Где нужно изменить

### 1. `desktop/auth_view.py` — Экран входа (строки 31-70)

**Текущее состояние:**
```python
error_text = ft.Text(
    value="",
    color=ft.Colors.RED,
    visible=False,
    font_family="Times New Roman"
)
# ...
error_text.value = "Введите логин и пароль"
error_text.visible = True
```

**Что нужно сделать:**
Создать функцию `show_notification()` и заменить `error_text` на `AlertDialog`:

```python
def show_notification(page: ft.Page, title: str, message: str, type: str = "error"):
    """Показать всплывающее уведомление"""
    colors = {
        "error": {"bg": "#FFEBEE", "title_bg": "#F44336", "icon": ft.Icons.ERROR},
        "warning": {"bg": "#FFF3E0", "title_bg": "#FF9800", "icon": ft.Icons.WARNING},
        "info": {"bg": "#E3F2FD", "title_bg": "#2196F3", "icon": ft.Icons.INFO}
    }
    style = colors.get(type, colors["error"])
    
    dialog = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(style["icon"], color="#FFFFFF"),
            ft.Text(title, color="#FFFFFF", weight=ft.FontWeight.BOLD)
        ]),
        title_padding=ft.padding.all(10),
        content=ft.Text(message, color="#000000"),
        bgcolor=style["bg"],
        actions=[
            ft.ElevatedButton("OK", on_click=lambda e: close_dialog(e, dialog))
        ]
    )
    # Установить цвет заголовка через Container wrapper
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
```

### 2. `desktop/products_view.py` — Форма редактирования товара (строки 533-626)

**Места для замены:**
- Строка 537-548: Валидация полей формы — заменить `raise ValueError` на показ диалога
- Строка 610-616: Ошибки валидации — заменить `SnackBar` на `AlertDialog`
- Строка 617-626: Общие ошибки — заменить `SnackBar` на `AlertDialog`

### 3. `desktop/orders_view.py` — Форма заказов (строки 383-458)

**Места для замены:**
- Строка 386-391: Валидация полей формы
- Строка 440-446: Ошибки валидации
- Строка 447-458: Общие ошибки

## Зависимости

| Компонент | Зависит от | Влияет на |
|-----------|------------|-----------|
| `show_notification()` | `flet` (ft.AlertDialog) | Все места с ошибками |
| `auth_view.py` | Новая функция уведомлений | Нет других зависимостей |
| `products_view.py` | Новая функция уведомлений | Нет других зависимостей |
| `orders_view.py` | Новая функция уведомлений | Нет других зависимостей |

## Почему это ничего не сломает

1. **Изолированность изменений**: Функция уведомлений — это UI-компонент, не затрагивающий бизнес-логику или работу с БД.

2. **Обратная совместимость**: `AlertDialog` в Flet работает как модальное окно и не блокирует основной поток приложения.

3. **Сохранение потока выполнения**: После закрытия диалога выполнение кода продолжается как обычно.

4. **Нет изменений в моделях данных**: Изменения касаются только слоя представления (View).

## Рекомендуемая реализация

Создать отдельный модуль `desktop/notifications.py`:

```python
"""Модуль уведомлений для десктопного приложения"""
import flet as ft

def show_error(page: ft.Page, message: str, title: str = "Ошибка"):
    """Показать ошибку"""
    _show_dialog(page, title, message, "#F44336", ft.Icons.ERROR)

def show_warning(page: ft.Page, message: str, title: str = "Предупреждение"):
    """Показать предупреждение"""
    _show_dialog(page, title, message, "#FF9800", ft.Icons.WARNING)

def show_info(page: ft.Page, message: str, title: str = "Информация"):
    """Показать информацию"""
    _show_dialog(page, title, message, "#4CAF50", ft.Icons.INFO)

def _show_dialog(page: ft.Page, title: str, message: str, color: str, icon):
    """Внутренняя функция показа диалога"""
    def close_dialog(e):
        dialog.open = False
        if dialog in page.overlay:
            page.overlay.remove(dialog)
        page.update()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="#FFFFFF", size=24),
                ft.Text(title, color="#FFFFFF", weight=ft.FontWeight.BOLD, size=16)
            ], spacing=10),
            bgcolor=color,
            padding=10,
            border_radius=ft.border_radius.only(top_left=5, top_right=5)
        ),
        content=ft.Container(
            content=ft.Text(message, color="#000000", size=14),
            padding=20
        ),
        actions=[
            ft.ElevatedButton(
                "OK",
                on_click=close_dialog,
                bgcolor="#00FA9A",
                color="#000000",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=5),
                    side=ft.BorderSide(2, "#000000")
                )
            )
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        bgcolor="#FFFFFF"
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
```

## Тестирование

1. Попробовать войти с пустым логином/паролем
2. Попробовать войти с неверными данными
3. Попробовать сохранить товар без обязательных полей
4. Попробовать сохранить заказ без адреса выдачи
5. Успешно сохранить товар/заказ и проверить информационное сообщение

