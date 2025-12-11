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
from PIL import Image
import uuid


# Глобальная переменная для отслеживания открытых форм редактирования
_open_form_dialog = None

def create_products_view(page: ft.Page, app_state):
    """Создание экрана товаров"""
    global _open_form_dialog
    
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
    
    # Элементы управления фильтров
    search_field = ft.TextField(
        label="Поиск",
        width=200,
        text_size=12,
        visible=role in ["manager", "admin"],
        on_change=lambda e: refresh_products(),
        bgcolor="#FFFFFF",
        border_color="#000000"
    )
    
    supplier_dropdown = ft.Dropdown(
        label="Поставщик",
        width=200,
        text_size=12,
        visible=role in ["manager", "admin"],
        options=[ft.dropdown.Option(key="", text="Все поставщики")] + [
            ft.dropdown.Option(key=str(s.id), text=s.name)
            for s in suppliers
        ],
        on_change=lambda e: refresh_products(),
        bgcolor="#FFFFFF",
        border_color="#000000"
    )
    
    sort_dropdown = ft.Dropdown(
        label="Сортировка",
        width=200,
        text_size=12,
        visible=role in ["manager", "admin"],
        options=[
            ft.dropdown.Option(key="", text="Без сортировки"),
            ft.dropdown.Option(key="asc", text="По возрастанию остатка"),
            ft.dropdown.Option(key="desc", text="По убыванию остатка")
        ],
        on_change=lambda e: refresh_products(),
        bgcolor="#FFFFFF",
        border_color="#000000"
    )
    
    # Контейнер для карточек товаров
    products_container = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
        expand=True
    )
    
    def refresh_products():
        """Обновление списка товаров"""
        refresh_db = SessionLocal()
        try:
            search = search_field.value if search_field.visible and search_field.value else None
            supplier_id = None
            if supplier_dropdown.visible and supplier_dropdown.value:
                value = supplier_dropdown.value.strip()
                if value and value != "" and value != "Все поставщики":
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
            
            products_container.controls.clear()
            
            if not products_list:
                products_container.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Товары не найдены",
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
            
            for product in products_list:
                try:
                    category_name = product.category.name if product.category else "Не указана"
                    manufacturer_name = product.manufacturer.name if product.manufacturer else "Не указан"
                    supplier_name = product.supplier.name if product.supplier else "Не указан"
                    
                    # Изображение товара
                    if product.image_path:
                        image_path = f"app/{product.image_path}"
                    else:
                        image_path = "app/static/images/picture.png"
                    
                    image_widget = ft.Container(
                        width=120,
                        height=120,
                        content=ft.Image(
                            src=image_path,
                            fit=ft.ImageFit.CONTAIN,
                            error_content=ft.Image(src="app/static/images/picture.png", fit=ft.ImageFit.CONTAIN)
                        ),
                        alignment=ft.alignment.center,
                        border=ft.border.all(1, "#000000")
                    )
                    
                    # Цена с учетом скидки
                    final_price = product.price * (1 - product.discount_percent / 100)
                    price_row = ft.Row(controls=[], spacing=5)
                    
                    if product.discount_percent > 0:
                        price_row.controls.append(
                            ft.Text(
                                f"{product.price:.0f} руб.",
                                size=12,
                                color="#FF0000",
                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                                font_family="Times New Roman"
                            )
                        )
                        price_row.controls.append(
                            ft.Text(
                                f"{final_price:.0f} руб.",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#000000",
                                font_family="Times New Roman"
                            )
                        )
                    else:
                        price_row.controls.append(
                            ft.Text(
                                f"{product.price:.0f} руб.",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#000000",
                                font_family="Times New Roman"
                            )
                        )
                    
                    # Информация о товаре (центральная часть)
                    info_column = ft.Column(
                        [
                            ft.Text(
                                f"{category_name} | {product.name}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            ft.Text(
                                f"Описание: {product.description or 'Нет описания'}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman",
                                max_lines=2
                            ),
                            ft.Text(
                                f"Производитель: {manufacturer_name}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            ft.Text(
                                f"Поставщик: {supplier_name}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            price_row,
                            ft.Text(
                                f"Ед. изм.: {product.unit}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                            ft.Text(
                                f"Количество на складе: {product.stock_quantity}",
                                size=11,
                                color="#000000",
                                font_family="Times New Roman"
                            ),
                        ],
                        spacing=2,
                        expand=True
                    )
                    
                    # Блок скидки справа (цвет зависит от процента)
                    discount_bg_color = "#2E8B57" if product.discount_percent > 15 else "#00FF00"
                    
                    discount_block = ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Скидка",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color="#000000",
                                    font_family="Times New Roman",
                                    text_align=ft.TextAlign.CENTER
                                ),
                                ft.Text(
                                    f"{product.discount_percent:.0f}%",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color="#000000",
                                    font_family="Times New Roman",
                                    text_align=ft.TextAlign.CENTER
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=5
                        ),
                        width=100,
                        height=120,
                        bgcolor=discount_bg_color,
                        border=ft.border.all(2, "#000000"),
                        alignment=ft.alignment.center
                    )
                    
                    # Карточка товара
                    product_card = ft.Container(
                        content=ft.Row(
                            [
                                image_widget,
                                ft.Container(
                                    content=info_column,
                                    expand=True,
                                    padding=10
                                ),
                                discount_block
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        bgcolor="#FFFFFF",
                        border=ft.border.all(2, "#000000"),
                        padding=5,
                        on_click=lambda e, p_id=product.id: edit_product(p_id) if role == "admin" else None,
                        data=product.id
                    )
                    
                    products_container.controls.append(product_card)
                except Exception as e:
                    print(f"Ошибка при обработке товара {product.id}: {e}")
                    continue
        except Exception as e:
            print(f"Ошибка при обновлении товаров: {e}")
            import traceback
            traceback.print_exc()
            
            products_container.controls.clear()
            products_container.controls.append(
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
        global _open_form_dialog
        
        if _open_form_dialog is not None:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Закройте текущее окно редактирования перед открытием нового"),
                bgcolor=ft.Colors.ORANGE
            )
            page.snack_bar.open = True
            page.update()
            return
        
        form_db = SessionLocal()
        try:
            product = get_product(form_db, product_id) if product_id else None
            
            next_id = None
            if not product_id:
                from app.models import Product as ProductModel
                last_product = form_db.query(ProductModel).order_by(ProductModel.id.desc()).first()
                next_id = (last_product.id + 1) if last_product else 1
            
            categories = get_categories(form_db)
            manufacturers = get_manufacturers(form_db)
            suppliers_list = get_suppliers(form_db)
            
            if not categories:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка: нет категорий в базе данных."),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
            
            if not manufacturers:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка: нет производителей в базе данных."),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
            
            if not suppliers_list:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка: нет поставщиков в базе данных."),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
            
            # Поля формы
            article_field = ft.TextField(
                label="Артикул",
                value=str(product.id) if product else str(next_id),
                read_only=True,
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            name_field = ft.TextField(
                label="Название",
                value=product.name if product else "",
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            unit_field = ft.TextField(
                label="Ед. изм.",
                value=product.unit if product else "шт",
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            price_field = ft.TextField(
                label="Цена",
                value=str(product.price) if product else "0",
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            supplier_form_dropdown = ft.Dropdown(
                label="Поставщик",
                options=[ft.dropdown.Option(key=str(s.id), text=s.name) for s in suppliers_list],
                value=str(product.supplier_id) if product else (str(suppliers_list[0].id) if suppliers_list else None),
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            manufacturer_dropdown = ft.Dropdown(
                label="Производитель",
                options=[ft.dropdown.Option(key=str(m.id), text=m.name) for m in manufacturers],
                value=str(product.manufacturer_id) if product else (str(manufacturers[0].id) if manufacturers else None),
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            category_dropdown = ft.Dropdown(
                label="Категория",
                options=[ft.dropdown.Option(key=str(c.id), text=c.name) for c in categories],
                value=str(product.category_id) if product else (str(categories[0].id) if categories else None),
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            discount_field = ft.TextField(
                label="Скидка (%)",
                value=str(product.discount_percent) if product else "0",
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            stock_field = ft.TextField(
                label="Количество на складе",
                value=str(product.stock_quantity) if product else "0",
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            description_field = ft.TextField(
                label="Описание",
                value=product.description if product else "",
                multiline=True,
                min_lines=2,
                max_lines=4,
                bgcolor="#FFFFFF",
                color="#000000",
                border_color="#000000",
                width=400
            )
            
            # Изображение
            image_file_picker = ft.FilePicker()
            page.overlay.append(image_file_picker)
            image_path_ref = [product.image_path if product else None]
            
            image_preview = ft.Container(
                width=200,
                height=150,
                content=ft.Image(
                    src=f"app/{product.image_path}" if product and product.image_path else "app/static/images/picture.png",
                    fit=ft.ImageFit.CONTAIN
                ),
                border=ft.border.all(1, "#000000"),
                alignment=ft.alignment.center
            )
            
            def on_image_picked(e: ft.FilePickerResultEvent):
                if e.files and len(e.files) > 0:
                    selected_file = e.files[0]
                    try:
                        image_path_ref[0] = selected_file.path
                        image_preview.content = ft.Image(
                            src=selected_file.path,
                            fit=ft.ImageFit.CONTAIN
                        )
                        page.update()
                    except Exception as ex:
                        print(f"Ошибка при загрузке изображения: {ex}")
            
            image_file_picker.on_result = on_image_picked
            
            def pick_image(e):
                image_file_picker.pick_files(
                    allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp"],
                    dialog_title="Выберите изображение товара"
                )
            
            image_picker_button = ft.ElevatedButton(
                "Выбрать фото",
                icon=ft.Icons.IMAGE,
                on_click=pick_image,
                bgcolor="#00FA9A",
                color="#000000",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=5),
                    side=ft.BorderSide(2, "#000000")
                )
            )
            
            def save_product(e):
                save_db = SessionLocal()
                try:
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
                    
                    saved_image_path = None
                    if image_path_ref[0]:
                        is_new_file = os.path.exists(image_path_ref[0]) and not image_path_ref[0].startswith("static/")
                        
                        if is_new_file:
                            try:
                                upload_dir = "app/static/images/products"
                                os.makedirs(upload_dir, exist_ok=True)
                                
                                target_id = product_id if product_id else next_id
                                
                                img = Image.open(image_path_ref[0])
                                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                                
                                file_ext = os.path.splitext(image_path_ref[0])[1] or ".jpg"
                                filename = f"product_{target_id}{file_ext}"
                                filepath = os.path.join(upload_dir, filename)
                                img.save(filepath)
                                
                                saved_image_path = f"static/images/products/{filename}"
                                
                                if product_id and product and product.image_path:
                                    old_path = f"app/{product.image_path}"
                                    if os.path.exists(old_path):
                                        try:
                                            os.remove(old_path)
                                        except Exception as ex:
                                            print(f"Ошибка удаления старого изображения: {ex}")
                            except Exception as ex:
                                print(f"Ошибка обработки изображения: {ex}")
                                raise ValueError(f"Ошибка обработки изображения: {str(ex)}")
                        elif product_id and product:
                            saved_image_path = product.image_path
                    
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
                        update_data = ProductUpdate(**product_data.dict())
                        update_product(save_db, product_id, update_data, image_path=saved_image_path)
                    else:
                        create_product(save_db, product_data, image_path=saved_image_path)
                    
                    global _open_form_dialog
                    _open_form_dialog = None
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
                global _open_form_dialog
                _open_form_dialog = None
                for overlay_item in list(page.overlay):
                    if isinstance(overlay_item, (ft.AlertDialog, ft.Container, ft.Stack)):
                        page.overlay.remove(overlay_item)
                page.update()
            
            def delete_product_action(e):
                if product_id:
                    close_dialog(e)
                    delete_product_confirm(product_id)
            
            # Кнопки внизу диалога
            buttons_row = ft.Row(
                [
                    ft.ElevatedButton(
                        "Сохранить",
                        on_click=save_product,
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
                    ft.ElevatedButton(
                        "Удалить товар",
                        on_click=delete_product_action,
                        bgcolor="#00FA9A",
                        color="#000000",
                        visible=product_id is not None,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                            side=ft.BorderSide(2, "#000000")
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
            
            # Диалог карточки товара
            form_dialog = ft.Container(
                content=ft.Column(
                    [
                        # Заголовок
                        ft.Container(
                            content=ft.Text(
                                "Карточка товара",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#000000",
                                font_family="Times New Roman",
                                text_align=ft.TextAlign.CENTER
                            ),
                            bgcolor="#00FF00",
                            padding=10,
                            width=450,
                            alignment=ft.alignment.center
                        ),
                        # Содержимое формы
                        ft.Container(
                            content=ft.Column(
                                [
                                    article_field,
                                    name_field,
                                    unit_field,
                                    price_field,
                                    supplier_form_dropdown,
                                    manufacturer_dropdown,
                                    category_dropdown,
                                    discount_field,
                                    stock_field,
                                    description_field,
                                    ft.Container(height=10),
                                    image_picker_button,
                                    image_preview,
                                ],
                                scroll=ft.ScrollMode.AUTO,
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            height=450,
                            width=430,
                            padding=10
                        ),
                        buttons_row
                    ],
                    spacing=5,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor="#FFFFFF",
                padding=10,
                width=470,
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
            
            _open_form_dialog = dialog_stack
            
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
            title=ft.Text("Подтверждение", color="#000000"),
            on_dismiss=lambda e: close_dialog(e) if confirm_dialog in page.overlay else None,
            bgcolor="#00FF00",
            content=ft.Text("Вы уверены, что хотите удалить этот товар?", color="#000000"),
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
    
    def on_back(e):
        """Обработчик кнопки Назад"""
        from desktop.auth_view import create_login_view
        page.views.clear()
        page.views.append(create_login_view(page, app_state))
        page.update()
    
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
    
    # Кастомный заголовок
    header = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "Каталог товаров",
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
    
    # Панель фильтров
    filters_row = ft.Container(
        content=ft.Row(
            [
                search_field,
                supplier_dropdown,
                sort_dropdown,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        ),
        bgcolor="#FFFFFF",
        padding=10,
        border=ft.border.all(1, "#000000"),
        visible=role in ["manager", "admin"]
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
                    "Добавить товар",
                    on_click=add_product,
                    visible=role == "admin",
                    bgcolor="#00FA9A",
                    color="#000000",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                        side=ft.BorderSide(2, "#000000")
                    )
                ),
                ft.ElevatedButton(
                    "Заказы",
                    on_click=navigate_to_orders,
                    visible=role in ["manager", "admin"],
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
    try:
        view = ft.View(
            route="/products",
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            header,
                            filters_row,
                            ft.Container(
                                content=products_container,
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
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при создании view: {e}")
        import traceback
        traceback.print_exc()
        view = ft.View(
            route="/products",
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Ошибка загрузки страницы",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#FF0000"
                            ),
                            ft.Text(
                                f"Детали: {str(e)}",
                                size=14,
                                color="#000000"
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            ],
            bgcolor="#FFFFFF"
        )
    
    return view
