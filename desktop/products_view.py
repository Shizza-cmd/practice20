"""
Модуль управления товарами для десктопного приложения
"""
import flet as ft
from app.database import SessionLocal
from app.services.product_service import (
    get_products, get_product, create_product, update_product,
    delete_product, get_categories, get_manufacturers, get_suppliers
)
from app.schemas import ProductCreate, ProductUpdate
import os


def create_products_view(page: ft.Page, app_state):
    """Создание экрана товаров"""
    
    db = SessionLocal()
    role = app_state.current_user.role if app_state.current_user else "guest"
    
    # Получение данных с обработкой ошибок
    try:
        products = get_products(db)
        suppliers = get_suppliers(db) if role in ["manager", "admin"] else []
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        products = []
        suppliers = []
    
    # Элементы управления
    search_field = ft.TextField(
        label="Поиск",
        width=300,
        visible=role in ["manager", "admin"]
    )
    
    supplier_dropdown = ft.Dropdown(
        label="Поставщик",
        width=200,
        visible=role in ["manager", "admin"],
        options=[ft.dropdown.Option(key="", text="Все")] + [
            ft.dropdown.Option(key=str(s.id), text=s.name)
            for s in suppliers
        ]
    )
    
    sort_dropdown = ft.Dropdown(
        label="Сортировка",
        width=200,
        visible=role in ["manager", "admin"],
        options=[
            ft.dropdown.Option(key="", text="Без сортировки"),
            ft.dropdown.Option(key="asc", text="По возрастанию остатка"),
            ft.dropdown.Option(key="desc", text="По убыванию остатка")
        ]
    )
    
    # Таблица товаров
    products_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Название")),
            ft.DataColumn(ft.Text("Категория")),
            ft.DataColumn(ft.Text("Производитель")),
            ft.DataColumn(ft.Text("Цена")),
            ft.DataColumn(ft.Text("Остаток")),
            ft.DataColumn(ft.Text("Действия")),
        ],
        rows=[],
        heading_row_color=ft.Colors.BLUE_700,
        heading_row_height=50,
    )
    
    def refresh_products():
        """Обновление списка товаров"""
        refresh_db = SessionLocal()
        try:
            search = search_field.value if search_field.visible and search_field.value else None
            # Проверяем, что выбрано не "Все" (пустое значение или текст "Все")
            supplier_id = None
            if supplier_dropdown.visible and supplier_dropdown.value:
                value = supplier_dropdown.value.strip()
                # Проверяем, что это не пустая строка и не текст "Все"
                if value and value != "Все":
                    try:
                        supplier_id = int(value)
                    except (ValueError, AttributeError):
                        supplier_id = None
            sort_by_stock = sort_dropdown.value if sort_dropdown.visible and sort_dropdown.value else None
            
            products_list = get_products(
                refresh_db,
                search=search,
                supplier_id=supplier_id,
                sort_by_stock=sort_by_stock
            )
            
            # Обрабатываем данные ДО закрытия соединения
            products_table.rows = []
            for product in products_list:
                try:
                    # Получаем данные связанных объектов пока соединение открыто
                    category_name = product.category.name if product.category else "Не указана"
                    manufacturer_name = product.manufacturer.name if product.manufacturer else "Не указан"
                    
                    image_widget = ft.Container(
                        width=50,
                        height=50,
                        content=ft.Image(
                            src=f"app/{product.image_path}" if product.image_path else None,
                            fit=ft.ImageFit.CONTAIN,
                            error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED)
                        ) if product.image_path else ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=50)
                    )
                    
                    actions = []
                    if role == "admin":
                        actions.append(
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Редактировать",
                                on_click=lambda e, p_id=product.id: edit_product(p_id)
                            )
                        )
                        actions.append(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Удалить",
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, p_id=product.id: delete_product_confirm(p_id)
                            )
                        )
                    
                    products_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(str(product.id))),
                                ft.DataCell(ft.Row([image_widget, ft.Text(product.name, width=200)])),
                                ft.DataCell(ft.Text(category_name)),
                                ft.DataCell(ft.Text(manufacturer_name)),
                                ft.DataCell(ft.Text(f"{product.price:.2f} ₽")),
                                ft.DataCell(ft.Text(str(product.stock_quantity))),
                                ft.DataCell(ft.Row(actions)),
                            ]
                        )
                    )
                except Exception as e:
                    print(f"Ошибка при обработке товара {product.id}: {e}")
                    continue
        except Exception as e:
            print(f"Ошибка при обновлении товаров: {e}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка загрузки данных: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
        finally:
            refresh_db.close()
        
        page.update()
    
    def add_product(e):
        """Открытие формы добавления товара"""
        try:
            open_product_form()
        except Exception as ex:
            print(f"Ошибка при открытии формы добавления товара: {ex}")
            import traceback
            traceback.print_exc()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка при открытии формы: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
    
    def edit_product(product_id: int):
        """Открытие формы редактирования товара"""
        open_product_form(product_id)
    
    def open_product_form(product_id: int = None):
        """Открытие формы товара"""
        form_db = SessionLocal()
        try:
            product = get_product(form_db, product_id) if product_id else None
            
            categories = get_categories(form_db)
            manufacturers = get_manufacturers(form_db)
            suppliers_list = get_suppliers(form_db)
            
            # Проверка наличия необходимых данных
            if not categories:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка: нет категорий в базе данных. Сначала создайте категории."),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
            
            if not manufacturers:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка: нет производителей в базе данных. Сначала создайте производителей."),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
            
            if not suppliers_list:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка: нет поставщиков в базе данных. Сначала создайте поставщиков."),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
            
            name_field = ft.TextField(
                label="Название", 
                value=product.name if product else "",
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            description_field = ft.TextField(
                label="Описание", 
                value=product.description if product else "", 
                multiline=True,
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            price_field = ft.TextField(
                label="Цена", 
                value=str(product.price) if product else "0", 
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            unit_field = ft.TextField(
                label="Единица измерения", 
                value=product.unit if product else "шт",
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            stock_field = ft.TextField(
                label="Остаток", 
                value=str(product.stock_quantity) if product else "0", 
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            discount_field = ft.TextField(
                label="Скидка %", 
                value=str(product.discount_percent) if product else "0", 
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            
            category_dropdown = ft.Dropdown(
                label="Категория",
                options=[ft.dropdown.Option(key=str(c.id), text=c.name) for c in categories],
                value=str(product.category_id) if product else (str(categories[0].id) if categories else None),
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            
            manufacturer_dropdown = ft.Dropdown(
                label="Производитель",
                options=[ft.dropdown.Option(key=str(m.id), text=m.name) for m in manufacturers],
                value=str(product.manufacturer_id) if product else (str(manufacturers[0].id) if manufacturers else None),
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            
            supplier_form_dropdown = ft.Dropdown(
                label="Поставщик",
                options=[ft.dropdown.Option(key=str(s.id), text=s.name) for s in suppliers_list],
                value=str(product.supplier_id) if product else (str(suppliers_list[0].id) if suppliers_list else None),
                bgcolor=ft.Colors.GREY_700,
                color=ft.Colors.WHITE
            )
            
            def save_product(e):
                save_db = SessionLocal()
                try:
                    # Валидация полей
                    if not name_field.value or not name_field.value.strip():
                        raise ValueError("Название товара обязательно")
                    if not category_dropdown.value:
                        raise ValueError("Выберите категорию")
                    if not manufacturer_dropdown.value:
                        raise ValueError("Выберите производителя")
                    if not supplier_form_dropdown.value:
                        raise ValueError("Выберите поставщика")
                    if not price_field.value or float(price_field.value) < 0:
                        raise ValueError("Цена должна быть положительным числом")
                    if not unit_field.value or not unit_field.value.strip():
                        raise ValueError("Единица измерения обязательна")
                    if not stock_field.value:
                        raise ValueError("Остаток обязателен")
                    
                    product_data = ProductCreate(
                        name=name_field.value.strip(),
                        category_id=int(category_dropdown.value),
                        description=description_field.value.strip() if description_field.value else None,
                        manufacturer_id=int(manufacturer_dropdown.value),
                        supplier_id=int(supplier_form_dropdown.value),
                        price=float(price_field.value),
                        unit=unit_field.value.strip(),
                        stock_quantity=int(stock_field.value),
                        discount_percent=float(discount_field.value or 0)
                    )
                    
                    if product_id:
                        update_product(save_db, product_id, ProductUpdate(**product_data.dict()))
                    else:
                        create_product(save_db, product_data)
                    
                    # Удаляем все диалоги из overlay
                    for overlay_item in list(page.overlay):
                        if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                            page.overlay.remove(overlay_item)
                    refresh_products()
                    page.update()
                except ValueError as ex:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Ошибка валидации: {str(ex)}"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
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
            form_dialog = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    "Редактировать товар" if product_id else "Добавить товар",
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
                                    name_field,
                                    description_field,
                                    category_dropdown,
                                    manufacturer_dropdown,
                                    supplier_form_dropdown,
                                    price_field,
                                    unit_field,
                                    stock_field,
                                    discount_field,
                                ],
                                scroll=ft.ScrollMode.AUTO,
                                spacing=10
                            ),
                            height=400,
                            width=500
                        ),
                        ft.Row(
                            [
                                ft.TextButton("Отмена", on_click=close_dialog, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                                ft.ElevatedButton("Сохранить", on_click=save_product, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
                            ],
                            alignment=ft.MainAxisAlignment.END
                        )
                    ],
                    spacing=10,
                    tight=True
                ),
                bgcolor=ft.Colors.GREY_900,
                padding=20,
                width=550,
                border_radius=10,
                border=ft.border.all(2, ft.Colors.GREY_600)
            )
            
            # Закрываем соединение перед открытием диалога
            # (save_product создаст свое соединение)
            form_db.close()
            
            # Очищаем старые диалоги и открываем новый
            # Удаляем все существующие диалоги
            for overlay_item in list(page.overlay):
                if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                    if hasattr(overlay_item, 'open'):
                        overlay_item.open = False
                    page.overlay.remove(overlay_item)
            
            # Позиционируем диалог по центру через Stack
            dialog_stack = ft.Stack(
                [
                    ft.Container(
                        content=form_dialog.content,
                        bgcolor=form_dialog.bgcolor,
                        padding=form_dialog.padding,
                        width=form_dialog.width,
                        border_radius=form_dialog.border_radius,
                        border=form_dialog.border,
                        left=page.width / 2 - 275,
                        top=page.height / 2 - 250,
                    )
                ],
                width=page.width,
                height=page.height
            )
            
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
    
    def delete_product_confirm(product_id: int):
        """Подтверждение удаления товара"""
        def close_dialog(e):
            confirm_dialog.open = False
            if confirm_dialog in page.overlay:
                page.overlay.remove(confirm_dialog)
            page.update()
        
        def confirm_delete(e):
            try:
                if delete_product(db, product_id):
                    refresh_products()
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Товар удален"),
                        bgcolor=ft.Colors.GREEN
                    )
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Ошибка удаления. Товар может быть в заказах."),
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
            title=ft.Text("Подтверждение"),
            on_dismiss=lambda e: close_dialog(e) if confirm_dialog in page.overlay else None,
            bgcolor=ft.Colors.GREY_900,
            title_style=ft.TextStyle(color=ft.Colors.WHITE),
            content=ft.Text("Вы уверены, что хотите удалить этот товар?", color=ft.Colors.WHITE),
            actions=[
                ft.TextButton("Отмена", on_click=close_dialog, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                ft.ElevatedButton("Удалить", on_click=confirm_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
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
    
    def on_search(e):
        """Обработчик поиска"""
        refresh_products()
    
    def on_logout(e):
        """Выход из системы"""
        from desktop.auth_view import create_login_view
        app_state.logout()
        page.views.clear()
        page.views.append(create_login_view(page, app_state))
        page.update()
    
    def navigate_to_orders(e):
        """Переход к заказам"""
        if app_state.current_user.role not in ["manager", "admin"]:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Доступ запрещен"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return
        
        from desktop.orders_view import create_orders_view
        page.views.clear()
        page.views.append(create_orders_view(page, app_state))
        page.update()
    
    # Инициализация таблицы
    try:
        refresh_products()
    except Exception as e:
        print(f"Ошибка при инициализации таблицы: {e}")
        import traceback
        traceback.print_exc()
    
    # Создание представления
    try:
        view = ft.View(
            route="/products",
        controls=[
            ft.AppBar(
                title=ft.Text("Товары"),
                bgcolor=ft.Colors.BLUE_700,
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Обновить",
                        on_click=lambda e: refresh_products()
                    ),
                    ft.PopupMenuButton(
                        items=[
                            *([ft.PopupMenuItem(
                                text="Заказы",
                                icon=ft.Icons.SHOPPING_CART,
                                on_click=navigate_to_orders
                            )] if role in ["manager", "admin"] else []),
                            ft.PopupMenuItem(),
                            ft.PopupMenuItem(
                                text="Выход",
                                icon=ft.Icons.LOGOUT,
                                on_click=on_logout
                            )
                        ]
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
                                    weight=ft.FontWeight.BOLD
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Row(
                            [
                                search_field,
                                supplier_dropdown,
                                sort_dropdown,
                                ft.ElevatedButton(
                                    "Поиск",
                                    on_click=on_search,
                                    visible=role in ["manager", "admin"]
                                ),
                                ft.ElevatedButton(
                                    "Добавить товар",
                                    icon=ft.Icons.ADD,
                                    on_click=add_product,
                                    visible=role == "admin"
                                )
                            ],
                            wrap=True
                        ),
                        ft.Container(
                            content=products_table,
                            expand=True,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=5,
                            padding=10
                        )
                    ],
                    expand=True,
                    spacing=10
                ),
                padding=20,
                expand=True
            )
        ]
    )
    except Exception as e:
        print(f"Ошибка при создании view: {e}")
        import traceback
        traceback.print_exc()
        # Возвращаем простой view с сообщением об ошибке
        view = ft.View(
            route="/products",
            controls=[
                ft.AppBar(title=ft.Text("Ошибка"), bgcolor=ft.Colors.RED),
                ft.Container(
                    content=ft.Text(f"Ошибка загрузки: {str(e)}"),
                    padding=20
                )
            ]
        )
    
    return view

