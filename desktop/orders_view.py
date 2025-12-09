"""
Модуль управления заказами для десктопного приложения
"""
import flet as ft
from app.database import SessionLocal
from app.services.order_service import get_orders, get_order, create_order, update_order, delete_order
from app.schemas import OrderCreate, OrderUpdate
from datetime import datetime
# Импорты перенесены внутрь функций для избежания циклических зависимостей


def create_orders_view(page: ft.Page, app_state):
    """Создание экрана заказов"""
    
    db = SessionLocal()
    role = app_state.current_user.role if app_state.current_user else "guest"
    
    if role not in ["manager", "admin"]:
        from desktop.products_view import create_products_view
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Доступ запрещен"),
            bgcolor=ft.Colors.RED
        )
        page.snack_bar.open = True
        page.update()
        return create_products_view(page, app_state)
    
    # Получение данных
    orders_list = get_orders(db)
    
    # Контейнер для карточек заказов
    orders_container = ft.Column(
        controls=[],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    def refresh_orders():
        """Обновление списка заказов"""
        refresh_db = SessionLocal()
        try:
            orders_list = get_orders(refresh_db)
            orders_container.controls.clear()
            
            for order in orders_list:
                # Создаем замыкание для корректной работы обработчиков
                def create_order_card(order_data):
                    # Действия для администратора
                    actions_row = ft.Row(controls=[], spacing=5)
                    if role == "admin":
                        actions_row.controls.append(
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Редактировать",
                                icon_color=ft.Colors.BLUE,
                                on_click=lambda e: edit_order(order_data.id)
                            )
                        )
                        actions_row.controls.append(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Удалить",
                                icon_color=ft.Colors.RED,
                                on_click=lambda e: delete_order_confirm(order_data.id)
                            )
                        )
                
                    # Создаем карточку заказа согласно макету
                    order_card = ft.Container(
                        content=ft.Row(
                            [
                                # Левая часть - информация о заказе
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("Артикул заказа", size=11, weight=ft.FontWeight.BOLD),
                                            ft.Text(order_data.article, size=12),
                                            ft.Text("Статус заказа", size=11, weight=ft.FontWeight.BOLD),
                                            ft.Text(order_data.status, size=12),
                                            ft.Text("Адрес пункта выдачи (текст)", size=11, weight=ft.FontWeight.BOLD),
                                            ft.Text(order_data.pickup_address, size=12, max_lines=3),
                                            ft.Text("Дата заказа", size=11, weight=ft.FontWeight.BOLD),
                                            ft.Text(order_data.order_date.strftime("%d.%m.%Y") if order_data.order_date else "", size=12),
                                            actions_row if role == "admin" else ft.Container()
                                        ],
                                        spacing=3
                                    ),
                                    expand=True,
                                    padding=10,
                                    border=ft.border.all(2, "#000000")
                                ),
                                # Правая часть - дата доставки
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                "Дата доставки",
                                                size=11,
                                                weight=ft.FontWeight.BOLD,
                                                font_family="Times New Roman",
                                                text_align=ft.TextAlign.CENTER
                                            ),
                                            ft.Container(height=20),
                                            ft.Text(
                                                order_data.delivery_date.strftime("%d.%m.%Y") if order_data.delivery_date else "Не указана",
                                                size=14,
                                                font_family="Times New Roman",
                                                text_align=ft.TextAlign.CENTER
                                            )
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        alignment=ft.MainAxisAlignment.START
                                    ),
                                    width=150,
                                    padding=10,
                                    border=ft.border.all(2, "#000000")
                                )
                            ],
                            spacing=0
                        ),
                        border=ft.border.all(2, "#000000"),
                        padding=0,
                        on_click=lambda e, order_id=order_data.id: edit_order(order_id) if role == "admin" else None
                    )
                    
                    return order_card
                
                # Создаем и добавляем карточку
                card = create_order_card(order)
                orders_container.controls.append(card)
            
            page.update()
        except Exception as e:
            print(f"Ошибка при обновлении заказов: {e}")
            import traceback
            traceback.print_exc()
        finally:
            refresh_db.close()
    
    def add_order(e):
        """Открытие формы добавления заказа"""
        try:
            open_order_form()
        except Exception as ex:
            print(f"Ошибка при открытии формы заказа: {ex}")
            import traceback
            traceback.print_exc()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка при открытии формы: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
    
    def edit_order(order_id: int):
        """Открытие формы редактирования заказа"""
        open_order_form(order_id)
    
    def open_order_form(order_id: int = None):
        """Открытие формы заказа"""
        order = get_order(db, order_id) if order_id else None
        
        article_field = ft.TextField(
            label="Артикул",
            value=order.article if order else "",
            bgcolor="#FFFFFF",
            color="#000000",
            border_color="#00FA9A"
        )
        
        status_dropdown = ft.Dropdown(
            label="Статус",
            options=[
                ft.dropdown.Option(key="новый", text="Новый"),
                ft.dropdown.Option(key="в обработке", text="В обработке"),
                ft.dropdown.Option(key="выполнен", text="Выполнен"),
                ft.dropdown.Option(key="отменен", text="Отменен"),
            ],
            value=order.status if order else "новый",
            bgcolor="#FFFFFF",
            color="#000000",
            border_color="#00FA9A"
        )
        
        pickup_field = ft.TextField(
            label="Адрес выдачи",
            value=order.pickup_address if order else "",
            multiline=True,
            bgcolor="#FFFFFF",
            color="#000000",
            border_color="#00FA9A"
        )
        
        order_date_field = ft.TextField(
            label="Дата заказа",
            value=order.order_date.strftime("%Y-%m-%dT%H:%M") if order and order.order_date else datetime.now().strftime("%Y-%m-%dT%H:%M"),
            bgcolor="#FFFFFF",
            color="#000000",
            border_color="#00FA9A"
        )
        
        delivery_date_field = ft.TextField(
            label="Дата доставки",
            value=order.delivery_date.strftime("%Y-%m-%dT%H:%M") if order and order.delivery_date else "",
            bgcolor="#FFFFFF",
            color="#000000",
            border_color="#00FA9A"
        )
        
        # Объявляем переменную для хранения ссылки на dialog_stack
        dialog_stack_ref = [None]  # Используем список для обхода ограничений nonlocal
        
        def save_order(e):
            print("save_order вызвана!")
            save_db = SessionLocal()
            try:
                print(f"Артикул: {article_field.value}")
                print(f"Статус: {status_dropdown.value}")
                print(f"Адрес: {pickup_field.value}")
                print(f"Дата заказа: {order_date_field.value}")
                
                # Валидация обязательных полей
                print("Начинаем валидацию...")
                if not article_field.value or not article_field.value.strip():
                    print("Ошибка: Артикул пустой")
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Артикул обязателен для заполнения"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                print("Артикул валиден")
                
                if not status_dropdown.value:
                    print("Ошибка: Статус пустой")
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Статус обязателен для заполнения"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                print("Статус валиден")
                
                if not pickup_field.value or not pickup_field.value.strip():
                    print("Ошибка: Адрес пустой")
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Адрес выдачи обязателен для заполнения"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                print("Адрес валиден")
                
                if not order_date_field.value:
                    print("Ошибка: Дата заказа пустая")
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Дата заказа обязательна для заполнения"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                print("Дата заказа валидна")
                
                # Парсинг дат
                print("Парсим дату заказа...")
                try:
                    # Пробуем разные форматы
                    order_date_str = order_date_field.value
                    print(f"Исходная дата: {order_date_str}")
                    
                    # Пробуем fromisoformat
                    try:
                        order_date = datetime.fromisoformat(order_date_str)
                        print(f"Дата заказа распарсена через fromisoformat: {order_date}")
                    except ValueError:
                        # Если не получилось, пробуем с заменой T на пробел
                        order_date_str_modified = order_date_str.replace("T", " ")
                        print(f"Пробуем формат с пробелом: {order_date_str_modified}")
                        # Пробуем strptime с разными форматами
                        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                            try:
                                order_date = datetime.strptime(order_date_str_modified, fmt)
                                print(f"Дата заказа распарсена через strptime ({fmt}): {order_date}")
                                break
                            except ValueError:
                                continue
                        else:
                            raise ValueError(f"Не удалось распарсить дату: {order_date_str}")
                except Exception as date_ex:
                    print(f"Ошибка парсинга даты заказа: {date_ex}")
                    import traceback
                    traceback.print_exc()
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Неверный формат даты заказа: {str(date_ex)}"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                
                delivery_date = None
                delivery_date_value = delivery_date_field.value.strip() if delivery_date_field.value else ""
                if delivery_date_value:
                    print(f"Парсим дату доставки: {delivery_date_value}")
                    try:
                        # Пробуем разные форматы для даты доставки
                        try:
                            delivery_date = datetime.fromisoformat(delivery_date_value)
                            print(f"Дата доставки распарсена через fromisoformat: {delivery_date}")
                        except ValueError:
                            # Если не получилось, пробуем с заменой T на пробел
                            delivery_date_str_modified = delivery_date_value.replace("T", " ")
                            print(f"Пробуем формат с пробелом: {delivery_date_str_modified}")
                            # Пробуем strptime с разными форматами
                            for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                                try:
                                    delivery_date = datetime.strptime(delivery_date_str_modified, fmt)
                                    print(f"Дата доставки распарсена через strptime ({fmt}): {delivery_date}")
                                    break
                                except ValueError:
                                    continue
                            else:
                                # Если не удалось распарсить, просто игнорируем (дата доставки не обязательна)
                                print(f"Не удалось распарсить дату доставки '{delivery_date_value}', игнорируем")
                                delivery_date = None
                    except Exception as date_ex:
                        # Если произошла какая-то другая ошибка, просто игнорируем дату доставки
                        print(f"Ошибка парсинга даты доставки (игнорируем): {date_ex}")
                        delivery_date = None
                else:
                    print("Дата доставки не указана")
                print("Парсинг дат завершен")
                print(f"Итоговые данные: order_date={order_date}, delivery_date={delivery_date}")
                
                # Сохранение заказа
                print(f"Сохранение заказа, order_id={order_id}")
                if order_id:
                    print("Обновление существующего заказа")
                    order_data = OrderUpdate(
                        article=article_field.value.strip(),
                        status=status_dropdown.value,
                        pickup_address=pickup_field.value.strip(),
                        order_date=order_date,
                        delivery_date=delivery_date
                    )
                    result = update_order(save_db, order_id, order_data)
                    print(f"Результат update_order: {result}")
                    if not result:
                        raise Exception("Заказ не найден")
                    message = "Заказ успешно обновлен"
                else:
                    print("Создание нового заказа")
                    order_data = OrderCreate(
                        article=article_field.value.strip(),
                        status=status_dropdown.value,
                        pickup_address=pickup_field.value.strip(),
                        order_date=order_date,
                        delivery_date=delivery_date,
                        items=[]  # Позиции заказа можно добавить позже
                    )
                    print(f"OrderCreate данные: {order_data}")
                    result = create_order(save_db, order_data)
                    print(f"Результат create_order: {result}")
                    if not result:
                        raise Exception("Не удалось создать заказ")
                    message = "Заказ успешно создан"
                
                print("Заказ сохранен, закрываем диалог")
                
                # Удаляем диалог из overlay
                print("Удаление диалогов из overlay")
                print(f"Текущее количество элементов в overlay: {len(page.overlay)}")
                
                # Удаляем dialog_stack если он есть
                if dialog_stack_ref[0] and dialog_stack_ref[0] in page.overlay:
                    print(f"Удаляем dialog_stack")
                    page.overlay.remove(dialog_stack_ref[0])
                
                # Также удаляем все остальные диалоги на всякий случай
                overlay_items_to_remove = []
                for overlay_item in list(page.overlay):
                    if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                        print(f"Найден элемент для удаления: {type(overlay_item)}")
                        overlay_items_to_remove.append(overlay_item)
                
                for item in overlay_items_to_remove:
                    print(f"Удаляем {type(item)}")
                    page.overlay.remove(item)
                
                print(f"Осталось элементов в overlay: {len(page.overlay)}")
                
                # Показываем сообщение об успехе
                print("Показываем сообщение об успехе")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.GREEN
                )
                page.snack_bar.open = True
                
                print("Обновляем список заказов")
                refresh_orders()
                print("Обновляем страницу")
                page.update()
                print("Готово!")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                print(f"Ошибка при сохранении заказа: {ex}")
                # Удаляем все диалоги из overlay
                for overlay_item in list(page.overlay):
                    if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                        page.overlay.remove(overlay_item)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Ошибка: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
            finally:
                save_db.close()
        
        def close_dialog(e):
            # Удаляем все диалоги из overlay
            for overlay_item in list(page.overlay):
                if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                    page.overlay.remove(overlay_item)
            page.update()
        
        # Создаем кастомный диалог через Container вместо AlertDialog
        form_dialog_content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Редактировать заказ" if order_id else "Добавить заказ",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=ft.Colors.WHITE,
                                on_click=close_dialog,
                                tooltip="Закрыть"
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                article_field,
                                status_dropdown,
                                pickup_field,
                                order_date_field,
                                delivery_date_field,
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=10
                        ),
                        height=300,
                        width=500
                    ),
                    ft.Row(
                        [
                            ft.TextButton("Отмена", on_click=close_dialog, style=ft.ButtonStyle(color="#000000")),
                            ft.ElevatedButton(
                                "Сохранить", 
                                on_click=save_order,
                                bgcolor=ft.Colors.BLUE_700, 
                                color=ft.Colors.WHITE
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END
                    )
                ],
                spacing=10,
                tight=True
            ),
            bgcolor="#7FFF00",
            padding=20,
            width=550,
            border_radius=10,
            border=ft.border.all(2, ft.Colors.GREY_600)
        )
        
        # Очищаем старые диалоги и открываем новый
        for overlay_item in list(page.overlay):
            if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                if hasattr(overlay_item, 'open'):
                    overlay_item.open = False
                page.overlay.remove(overlay_item)
        
        # Позиционируем диалог по центру через Stack с alignment
        # Используем сам form_dialog_content, чтобы сохранить все обработчики событий
        dialog_stack = ft.Stack(
            [
                form_dialog_content
            ],
            width=page.width,
            height=page.height,
            alignment=ft.alignment.center
        )
        
        # Сохраняем ссылку для доступа из save_order
        dialog_stack_ref[0] = dialog_stack
        
        page.overlay.append(dialog_stack)
        page.update()
    
    def delete_order_confirm(order_id: int):
        """Подтверждение удаления заказа"""
        def close_dialog(e):
            confirm_dialog.open = False
            if confirm_dialog in page.overlay:
                page.overlay.remove(confirm_dialog)
            page.update()
        
        def confirm_delete(e):
            try:
                if delete_order(db, order_id):
                    refresh_orders()
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Заказ удален"),
                        bgcolor=ft.Colors.GREEN
                    )
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Ошибка удаления"),
                        bgcolor=ft.Colors.RED
                    )
                page.snack_bar.open = True
                confirm_dialog.open = False
                if confirm_dialog in page.overlay:
                    page.overlay.remove(confirm_dialog)
                page.update()
            except Exception as ex:
                confirm_dialog.open = False
                if confirm_dialog in page.overlay:
                    page.overlay.remove(confirm_dialog)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Ошибка: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
        
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Подтверждение", color="#000000"),
            on_dismiss=lambda e: close_dialog(e) if confirm_dialog in page.overlay else None,
            bgcolor="#7FFF00",
            content=ft.Text("Вы уверены, что хотите удалить этот заказ?", color="#000000"),
            actions=[
                ft.TextButton("Отмена", on_click=close_dialog, style=ft.ButtonStyle(color="#000000")),
                ft.ElevatedButton("Удалить", on_click=confirm_delete, bgcolor=ft.Colors.RED, color="#000000")
            ]
        )
        
        # Очищаем старые диалоги и открываем новый
        # Удаляем все существующие диалоги
        for overlay_item in list(page.overlay):
            if isinstance(overlay_item, ft.AlertDialog):
                overlay_item.open = False
                page.overlay.remove(overlay_item)
        
        page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        page.update()
    
    def on_logout(e):
        """Выход из системы"""
        from desktop.auth_view import create_login_view
        app_state.logout()
        page.views.clear()
        page.views.append(create_login_view(page, app_state))
        page.update()
    
    def on_back(e):
        """Обработчик кнопки Назад"""
        from desktop.products_view import create_products_view
        page.views.clear()
        page.views.append(create_products_view(page, app_state))
        page.update()
    
    def navigate_to_products(e):
        """Переход к товарам"""
        from desktop.products_view import create_products_view
        page.views.clear()
        page.views.append(create_products_view(page, app_state))
        page.update()
    
    # Инициализация таблицы
    refresh_orders()
    
    # Создание представления
    view = ft.View(
        route="/orders",
        controls=[
            ft.AppBar(
                title=ft.Text("Заказы"),
                bgcolor="#00FA9A",  # Акцентирование внимания
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Назад",
                        on_click=on_back,
                        icon_color="#000000"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Обновить",
                        on_click=lambda e: refresh_orders(),
                        icon_color="#000000"
                    ),
                    ft.PopupMenuButton(
                        items=[
                            ft.PopupMenuItem(
                                text="Товары",
                                icon=ft.Icons.INVENTORY,
                                on_click=navigate_to_products
                            ),
                            *([ft.PopupMenuItem(
                                text="Импорт данных",
                                icon=ft.Icons.UPLOAD,
                                on_click=lambda e: (
                                    page.views.clear(),
                                    page.views.append(
                                        __import__("desktop.import_view", fromlist=["create_import_view"]).create_import_view(page, app_state)
                                    ),
                                    page.update()
                                )
                            )] if role == "admin" else []),
                            ft.PopupMenuItem(),
                            ft.PopupMenuItem(
                                text="Выход",
                                icon=ft.Icons.LOGOUT,
                                on_click=on_logout
                            )
                        ],
                        icon_color="#000000"
                    )
                ]
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    f"Пользователь: {app_state.current_user.full_name}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Times New Roman"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Добавить заказ",
                                    icon=ft.Icons.ADD,
                                    on_click=add_order,
                                    visible=role == "admin",
                                    bgcolor="#00FA9A",  # Акцентирование внимания
                                    color="#000000"
                                )
                            ]
                        ),
                        orders_container
                    ],
                    expand=True,
                    spacing=10
                ),
                padding=20,
                expand=True
            )
        ]
    )
    
    return view

