"""
Модуль управления заказами для десктопного приложения
"""
import flet as ft
from app.database import SessionLocal
from app.services.order_service import get_orders, get_order, create_order, update_order, delete_order
from app.services.product_service import get_products, get_pickup_points, get_product_by_article
from app.schemas import OrderCreate, OrderUpdate
from desktop.notifications import show_error, show_warning, show_info
from datetime import datetime


def create_orders_view(page: ft.Page, app_state):
    """Создание экрана заказов"""
    
    db = SessionLocal()
    role = app_state.current_user.role if app_state.current_user else "guest"
    
    if role not in ["manager", "admin"]:
        from desktop.products_view import create_products_view
        show_error(page, "Доступ запрещен")
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
                                f"Артикул заказа: {order_data.article}",
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
            show_error(page, f"Ошибка при открытии формы: {str(ex)}")
    
    def edit_order(order_id: int):
        """Открытие формы редактирования заказа"""
        open_order_form(order_id)
    
    def open_order_form(order_id: int = None):
        """Открытие формы заказа"""
        form_db = SessionLocal()
        try:
            order = get_order(form_db, order_id) if order_id else None
            products_list = get_products(form_db)
            pickup_points_list = get_pickup_points(form_db)
            
            # Список выбранных товаров: [{'article': 'XXX', 'quantity': N}, ...]
            selected_items = []
            
            # Парсинг существующих товаров из заказа (формат: "ART1, QTY1, ART2, QTY2")
            if order and order.article:
                parts = [p.strip() for p in order.article.split(',')]
                for i in range(0, len(parts) - 1, 2):
                    try:
                        article = parts[i]
                        qty = int(parts[i + 1])
                        selected_items.append({'article': article, 'quantity': qty})
                    except (ValueError, IndexError):
                        pass
            
            # Контейнер для отображения выбранных товаров (со скроллом)
            items_list_container = ft.Column(
                controls=[], 
                spacing=2,
                scroll=ft.ScrollMode.AUTO
            )
            
            def refresh_items_list():
                """Обновить отображение списка товаров"""
                items_list_container.controls.clear()
                if not selected_items:
                    items_list_container.controls.append(
                        ft.Text(
                            "Нет добавленных товаров",
                            size=11,
                            color="#666666",
                            italic=True
                        )
                    )
                else:
                    for idx, item in enumerate(selected_items):
                        # Найти название товара
                        product = next((p for p in products_list if p.article == item['article']), None)
                        product_name = product.name if product else "?"
                        
                        item_row = ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            f"{idx + 1}",
                                            size=10,
                                            color="#FFFFFF",
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        width=20,
                                        height=20,
                                        bgcolor="#00AA00",
                                        border_radius=10,
                                        alignment=ft.alignment.center
                                    ),
                                    ft.Text(
                                        f"{item['article']} - {product_name}",
                                        size=11,
                                        color="#000000",
                                        expand=True
                                    ),
                                    ft.Text(
                                        f"× {item['quantity']}",
                                        size=11,
                                        color="#000000",
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_size=16,
                                        icon_color="#FF0000",
                                        tooltip="Удалить",
                                        on_click=lambda e, i=idx: remove_item(i)
                                    )
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=ft.padding.symmetric(vertical=4, horizontal=5),
                            border=ft.border.only(bottom=ft.BorderSide(1, "#DDDDDD")) if idx < len(selected_items) - 1 else None
                        )
                        items_list_container.controls.append(item_row)
                page.update()
            
            def remove_item(idx):
                """Удалить товар из списка"""
                if 0 <= idx < len(selected_items):
                    selected_items.pop(idx)
                    refresh_items_list()
            
            # Dropdown для выбора артикула
            article_dropdown = ft.Dropdown(
                label="Артикул товара",
                options=[
                    ft.dropdown.Option(
                        key=p.article, 
                        text=f"{p.article} - {p.name}"
                    ) for p in products_list
                ],
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=200
            )
            
            # Поле количества
            quantity_field = ft.TextField(
                label="Кол-во",
                value="1",
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=70
            )
            
            def add_item_to_order(e):
                """Добавить товар в заказ"""
                if not article_dropdown.value:
                    show_warning(page, "Выберите артикул товара")
                    return
                if not quantity_field.value or int(quantity_field.value) < 1:
                    show_warning(page, "Укажите количество (≥1)")
                    return
                
                # Проверка на дубликат
                existing = next((item for item in selected_items if item['article'] == article_dropdown.value), None)
                if existing:
                    existing['quantity'] += int(quantity_field.value)
                else:
                    selected_items.append({
                        'article': article_dropdown.value,
                        'quantity': int(quantity_field.value)
                    })
                
                article_dropdown.value = None
                quantity_field.value = "1"
                refresh_items_list()
            
            # Строка добавления товара
            add_item_row = ft.Row(
                [
                    article_dropdown,
                    quantity_field,
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE,
                        icon_size=24,
                        icon_color="#00AA00",
                        tooltip="Добавить товар",
                        on_click=add_item_to_order
                    )
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            )
            
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
            
            # Dropdown для выбора пункта выдачи
            pickup_dropdown = ft.Dropdown(
                label="Адрес пункта выдачи *",
                options=[
                    ft.dropdown.Option(
                        key=pp.address, 
                        text=pp.address
                    ) for pp in pickup_points_list
                ],
                value=order.pickup_address if order else None,
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
            
            # Инициализация списка товаров
            refresh_items_list()
            
            dialog_stack_ref = [None]
            
            def save_order(e):
                save_db = SessionLocal()
                try:
                    # Валидация обязательных полей
                    if not selected_items:
                        raise ValueError("Добавьте хотя бы один товар")
                    if not status_dropdown.value:
                        raise ValueError("Статус обязателен")
                    if not pickup_dropdown.value:
                        raise ValueError("Адрес пункта выдачи обязателен")
                    if not order_date_field.value:
                        raise ValueError("Дата заказа обязательна")
                    
                    # Проверка существования всех товаров
                    for item in selected_items:
                        product = get_product_by_article(save_db, item['article'])
                        if not product:
                            raise ValueError(f"Товар с артикулом {item['article']} не найден")
                    
                    # Формирование строки артикулов: "ART1, QTY1, ART2, QTY2"
                    article_parts = []
                    for item in selected_items:
                        article_parts.append(item['article'])
                        article_parts.append(str(item['quantity']))
                    article_string = ', '.join(article_parts)
                    
                    # Парсинг дат
                    order_date = datetime.strptime(order_date_field.value, "%Y-%m-%d")
                    
                    delivery_date = None
                    if delivery_date_field.value and delivery_date_field.value.strip():
                        delivery_date = datetime.strptime(delivery_date_field.value.strip(), "%Y-%m-%d")
                    
                    if order_id:
                        order_data = OrderUpdate(
                            article=article_string,
                            status=status_dropdown.value,
                            pickup_address=pickup_dropdown.value,
                            order_date=order_date,
                            delivery_date=delivery_date
                        )
                        result = update_order(save_db, order_id, order_data)
                        if not result:
                            raise Exception("Заказ не найден")
                    else:
                        order_data = OrderCreate(
                            article=article_string,
                            status=status_dropdown.value,
                            pickup_address=pickup_dropdown.value,
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
                    
                    refresh_orders()
                    page.update()
                    show_info(page, "Заказ успешно сохранен")
                except ValueError as ex:
                    show_error(page, f"Ошибка: {str(ex)}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    for overlay_item in list(page.overlay):
                        if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                            page.overlay.remove(overlay_item)
                    show_error(page, f"Ошибка: {str(ex)}")
                finally:
                    save_db.close()
            
            def close_dialog(e):
                for overlay_item in list(page.overlay):
                    if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                        page.overlay.remove(overlay_item)
                page.update()
            
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
                                    ft.Text(
                                        "Товары заказа:",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color="#000000"
                                    ),
                                    add_item_row,
                                    ft.Container(
                                        content=items_list_container,
                                        height=100,
                                        border=ft.border.all(1, "#CCCCCC"),
                                        padding=5,
                                        bgcolor="#FAFAFA"
                                    ),
                                    ft.Divider(height=10),
                                    status_dropdown,
                                    pickup_dropdown,
                                    order_date_field,
                                    delivery_date_field,
                                ],
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            height=450,
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
            show_error(page, f"Ошибка при загрузке формы: {str(ex)}")
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
                    confirm_dialog.open = False
                    if confirm_dialog in page.overlay:
                        page.overlay.remove(confirm_dialog)
                    page.update()
                    show_info(page, "Заказ успешно удален")
                else:
                    confirm_dialog.open = False
                    if confirm_dialog in page.overlay:
                        page.overlay.remove(confirm_dialog)
                    page.update()
                    show_error(page, "Ошибка удаления")
            except Exception as ex:
                confirm_dialog.open = False
                if confirm_dialog in page.overlay:
                    page.overlay.remove(confirm_dialog)
                page.update()
                show_error(page, f"Ошибка: {str(ex)}")
        
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
