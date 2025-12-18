"""
Модуль управления заказами для десктопного приложения
"""
import flet as ft
from app.database import SessionLocal
from app.services.order_service import get_orders, get_order, create_order, update_order, delete_order
from app.services.product_service import get_products
from app.schemas import OrderCreate, OrderUpdate
from datetime import datetime


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
            
            if not orders_list:
                orders_container.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Заказы не найдены",
                            size=16,
                            color="#666666",
                            font_family="Times New Roman"
                        ),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
                page.update()
                return
            
            for order in orders_list:
                def create_order_card(order_data):
                    # Информация о заказе (левая часть)
                    info_column = ft.Column(
                        [
                            ft.Text(
                                f"Артикул заказа: {order_data.id}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            ft.Text(
                                f"Статус заказа: {order_data.status}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            ft.Text(
                                f"Адрес пункта выдачи: {order_data.pickup_address}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman",
                                max_lines=2
                            ),
                            ft.Text(
                                f"Дата заказа: {order_data.order_date.strftime('%Y-%m-%d') if order_data.order_date else 'Не указана'}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            ft.Text(
                                f"Дата заказа: {order_data.code if order_data.code else order_data.id }",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                        ],
                        spacing=3,
                        expand=True
                    )
                    
                    # Блок даты доставки справа (зеленый фон)
                    delivery_block = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Дата доставки:",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color="#000000",
                                    font_family="Times New Roman",
                                    text_align=ft.TextAlign.CENTER
                                ),
                                ft.Text(
                                    order_data.delivery_date.strftime('%Y-%m-%d') if order_data.delivery_date else "Не указана",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color="#000000",
                                    font_family="Times New Roman",
                                    text_align=ft.TextAlign.CENTER
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        ),
                        width=120,
                        height=80,
                        bgcolor="#00FF00",
                        border=ft.border.all(2, "#000000"),
                        alignment=ft.alignment.center,
                        padding=5
                    )
                    
                    # Карточка заказа
                    order_card = ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=info_column,
                                    expand=True,
                                    padding=10,
                                    border=ft.border.only(right=ft.BorderSide(2, "#000000"))
                                ),
                                delivery_block
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        bgcolor="#FFFFFF",
                        border=ft.border.all(2, "#000000"),
                        padding=0,
                        on_click=lambda e, order_id=order_data.id: edit_order(order_id) if role == "admin" else None
                    )
                    
                    return order_card
                
                card = create_order_card(order)
                orders_container.controls.append(card)
            
            page.update()
        except Exception as e:
            print(f"Ошибка при обновлении заказов: {e}")
            import traceback
            traceback.print_exc()
            
            orders_container.controls.clear()
            orders_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"Ошибка загрузки данных: {str(e)}",
                        size=14,
                        color="#FF0000",
                        font_family="Times New Roman"
                    ),
                    padding=20
                )
            )
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
        form_db = SessionLocal()
        try:
            order = get_order(form_db, order_id) if order_id else None
            products_list = get_products(form_db)
            
            # Поля формы
            status_dropdown = ft.Dropdown(
                label="Статус",
                options=[
                    ft.dropdown.Option(key="Новый", text="Новый"),
                    ft.dropdown.Option(key="В обработке", text="В обработке"),
                    ft.dropdown.Option(key="Завершен", text="Завершен"),
                    ft.dropdown.Option(key="Отменен", text="Отменен"),
                ],
                value=order.status if order else "Новый",
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=350
            )
            
            pickup_field = ft.TextField(
                label="Адрес пункта выдачи",
                value=order.pickup_address if order else "",
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=350
            )
            
            order_date_field = ft.TextField(
                label="Дата заказа",
                value=order.order_date.strftime("%Y-%m-%d") if order and order.order_date else datetime.now().strftime("%Y-%m-%d"),
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=350
            )
            
            delivery_date_field = ft.TextField(
                label="Дата доставки",
                value=order.delivery_date.strftime("%Y-%m-%d") if order and order.delivery_date else "",
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=350
            )
            
            # Товары заказа
            order_items_container = ft.Column(
                controls=[],
                spacing=5
            )
            
            selected_products = []
            
            def refresh_order_items():
                order_items_container.controls.clear()
                if not selected_products:
                    order_items_container.controls.append(
                        ft.Text(
                            "Нет добавленных товаров",
                            size=12,
                            color="#666666",
                            font_family="Times New Roman",
                            italic=True
                        )
                    )
                else:
                    for idx, item in enumerate(selected_products):
                        item_row = ft.Row(
                            [
                                ft.Text(
                                    f"{item['name']} x {item['quantity']}",
                                    size=12,
                                    color="#000000",
                                    font_family="Times New Roman",
                                    expand=True
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_size=16,
                                    icon_color="#FF0000",
                                    tooltip="Удалить",
                                    on_click=lambda e, i=idx: remove_product(i)
                                )
                            ],
                            spacing=5
                        )
                        order_items_container.controls.append(item_row)
                page.update()
            
            def remove_product(idx):
                if 0 <= idx < len(selected_products):
                    selected_products.pop(idx)
                    refresh_order_items()
            
            # Диалог добавления товара
            def show_add_product_dialog(e):
                product_dropdown = ft.Dropdown(
                    label="Товар",
                    options=[ft.dropdown.Option(key=str(p.id), text=p.name) for p in products_list],
                    width=300,
                    bgcolor="#FFFFFF",
                    color="#000000",
                    border_color="#000000"
                )
                
                quantity_field = ft.TextField(
                    label="Количество",
                    value="1",
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=100,
                    bgcolor="#FFFFFF",
                    color="#000000",
                    border_color="#000000"
                )
                
                def add_product_to_order(e):
                    if product_dropdown.value and quantity_field.value:
                        product = next((p for p in products_list if str(p.id) == product_dropdown.value), None)
                        if product:
                            selected_products.append({
                                'id': product.id,
                                'name': product.name,
                                'quantity': int(quantity_field.value)
                            })
                            refresh_order_items()
                    add_product_dialog.open = False
                    page.update()
                
                def close_add_dialog(e):
                    add_product_dialog.open = False
                    page.update()
                
                add_product_dialog = ft.AlertDialog(
                    title=ft.Text("Добавить товар", color="#000000"),
                    bgcolor="#00FF00",
                    content=ft.Column(
                        [
                            product_dropdown,
                            quantity_field
                        ],
                        spacing=10,
                        tight=True
                    ),
                    actions=[
                        ft.ElevatedButton(
                            "Отмена",
                            on_click=close_add_dialog,
                            bgcolor="#00FA9A",
                            color="#000000",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=5),
                                side=ft.BorderSide(2, "#000000")
                            )
                        ),
                        ft.ElevatedButton(
                            "Добавить",
                            on_click=add_product_to_order,
                            bgcolor="#00FA9A",
                            color="#000000",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=5),
                                side=ft.BorderSide(2, "#000000")
                            )
                        )
                    ]
                )
                
                page.overlay.append(add_product_dialog)
                add_product_dialog.open = True
                page.update()
            
            refresh_order_items()
            
            dialog_stack_ref = [None]
            
            def save_order(e):
                save_db = SessionLocal()
                try:
                    if not status_dropdown.value:
                        raise ValueError("Статус обязателен")
                    if not pickup_field.value or not pickup_field.value.strip():
                        raise ValueError("Адрес пункта выдачи обязателен")
                    if not order_date_field.value:
                        raise ValueError("Дата заказа обязательна")
                    
                    # Парсинг дат
                    order_date = datetime.strptime(order_date_field.value, "%Y-%m-%d")
                    
                    delivery_date = None
                    if delivery_date_field.value and delivery_date_field.value.strip():
                        delivery_date = datetime.strptime(delivery_date_field.value.strip(), "%Y-%m-%d")
                    
                    if order_id:
                        order_data = OrderUpdate(
                            article=str(order_id),
                            status=status_dropdown.value,
                            pickup_address=pickup_field.value.strip(),
                            order_date=order_date,
                            delivery_date=delivery_date
                        )
                        result = update_order(save_db, order_id, order_data)
                        if not result:
                            raise Exception("Заказ не найден")
                    else:
                        order_data = OrderCreate(
                            article=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            status=status_dropdown.value,
                            pickup_address=pickup_field.value.strip(),
                            order_date=order_date,
                            delivery_date=delivery_date,
                            items=[]
                        )
                        result = create_order(save_db, order_data)
                        if not result:
                            raise Exception("Не удалось создать заказ")
                    
                    # Закрываем диалог
                    if dialog_stack_ref[0] and dialog_stack_ref[0] in page.overlay:
                        page.overlay.remove(dialog_stack_ref[0])
                    
                    for overlay_item in list(page.overlay):
                        if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                            page.overlay.remove(overlay_item)
                    
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Заказ сохранен"),
                        bgcolor=ft.Colors.GREEN
                    )
                    page.snack_bar.open = True
                    
                    refresh_orders()
                    page.update()
                except ValueError as ex:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Ошибка: {str(ex)}"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
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
                for overlay_item in list(page.overlay):
                    if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                        page.overlay.remove(overlay_item)
                page.update()
            
            # Кнопки
            buttons_row = ft.Row(
                [
                    ft.ElevatedButton(
                        "Добавить товар",
                        on_click=show_add_product_dialog,
                        bgcolor="#00FA9A",
                        color="#000000",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            side=ft.BorderSide(2, "#000000")
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
            
            action_buttons_row = ft.Row(
                [
                    ft.ElevatedButton(
                        "Сохранить",
                        on_click=save_order,
                        bgcolor="#00FA9A",
                        color="#000000",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            side=ft.BorderSide(2, "#000000")
                        )
                    ),
                    ft.ElevatedButton(
                        "Отмена",
                        on_click=close_dialog,
                        bgcolor="#00FA9A",
                        color="#000000",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            side=ft.BorderSide(2, "#000000")
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
            
            # Диалог карточки заказа
            form_dialog = ft.Container(
                content=ft.Column(
                    [
                        # Заголовок
                        ft.Container(
                            content=ft.Text(
                                "Карточка заказа",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#000000",
                                font_family="Times New Roman",
                                text_align=ft.TextAlign.CENTER
                            ),
                            bgcolor="#00FF00",
                            padding=10,
                            width=400,
                            alignment=ft.alignment.center
                        ),
                        # Содержимое формы
                        ft.Container(
                            content=ft.Column(
                                [
                                    status_dropdown,
                                    pickup_field,
                                    order_date_field,
                                    delivery_date_field,
                                    ft.Container(height=10),
                                    ft.Text(
                                        "Товары заказа:",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color="#000000",
                                        font_family="Times New Roman"
                                    ),
                                    ft.Container(
                                        content=order_items_container,
                                        height=100,
                                        border=ft.border.all(1, "#CCCCCC"),
                                        padding=5
                                    ),
                                    buttons_row,
                                ],
                                scroll=ft.ScrollMode.AUTO,
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            height=380,
                            width=380,
                            padding=10
                        ),
                        action_buttons_row
                    ],
                    spacing=5,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor="#FFFFFF",
                padding=10,
                width=420,
                border_radius=0,
                border=ft.border.all(2, "#000000")
            )
            
            form_db.close()
            
            for overlay_item in list(page.overlay):
                if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                    if hasattr(overlay_item, 'open'):
                        overlay_item.open = False
                    page.overlay.remove(overlay_item)
            
            dialog_stack = ft.Stack(
                [
                    ft.Container(
                        content=form_dialog,
                        alignment=ft.alignment.center,
                        expand=True
                    )
                ],
                expand=True
            )
            
            dialog_stack_ref[0] = dialog_stack
            
            page.overlay.append(dialog_stack)
            page.update()
        except Exception as ex:
            if form_db:
                form_db.close()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка при загрузке формы: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            import traceback
            traceback.print_exc()
    
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
            bgcolor="#00FF00",
            content=ft.Text("Вы уверены, что хотите удалить этот заказ?", color="#000000"),
            actions=[
                ft.ElevatedButton(
                    "Отмена",
                    on_click=close_dialog,
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                ),
                ft.ElevatedButton(
                    "Удалить",
                    on_click=confirm_delete,
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                )
            ]
        )
        
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
    
    # Инициализация
    refresh_orders()
    
    # Кастомный заголовок
    header = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "Заказы",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="#000000",
                    font_family="Times New Roman"
                ),
                ft.Text(
                    f"{app_state.current_user.full_name if app_state.current_user else 'Гость'}",
                    size=16,
                    color="#000000",
                    font_family="Times New Roman"
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor="#00FF00",
        padding=15,
        border=ft.border.all(2, "#000000")
    )
    
    # Нижняя панель с кнопками
    bottom_buttons = ft.Container(
        content=ft.Row(
            [
                ft.ElevatedButton(
                    "Назад",
                    on_click=on_back,
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                ),
                ft.ElevatedButton(
                    "Добавить заказ",
                    on_click=add_order,
                    visible=role == "admin",
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                ),
                ft.ElevatedButton(
                    "Товары",
                    on_click=navigate_to_products,
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                ),
                ft.ElevatedButton(
                    "Выход",
                    on_click=on_logout,
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10
        ),
        bgcolor="#FFFFFF",
        padding=10,
        border=ft.border.all(1, "#000000")
    )
    
    # Создание представления без AppBar
    view = ft.View(
        route="/orders",
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        header,
                        ft.Container(
                            content=orders_container,
                            expand=True,
                            border=ft.border.all(1, "#000000"),
                            padding=5,
                            bgcolor="#FFFFFF"
                        ),
                        bottom_buttons
                    ],
                    expand=True,
                    spacing=5
                ),
                padding=10,
                expand=True,
                bgcolor="#FFFFFF"
            )
        ],
        bgcolor="#FFFFFF"
    )
    
    return view
