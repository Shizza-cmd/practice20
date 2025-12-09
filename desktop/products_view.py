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
    
    # Элементы управления
    search_field = ft.TextField(
        label="Поиск",
        width=300,
        visible=role in ["manager", "admin"],
        on_change=lambda e: refresh_products()  # Поиск в реальном времени
    )
    
    supplier_dropdown = ft.Dropdown(
        label="Поставщик",
        width=200,
        visible=role in ["manager", "admin"],
        options=[ft.dropdown.Option(key="", text="Все поставщики")] + [
            ft.dropdown.Option(key=str(s.id), text=s.name)
            for s in suppliers
        ],
        on_change=lambda e: refresh_products()  # Фильтрация в реальном времени
    )
    
    sort_dropdown = ft.Dropdown(
        label="Сортировка",
        width=200,
        visible=role in ["manager", "admin"],
        options=[
            ft.dropdown.Option(key="", text="Без сортировки"),
            ft.dropdown.Option(key="asc", text="По возрастанию остатка"),
            ft.dropdown.Option(key="desc", text="По убыванию остатка")
        ],
        on_change=lambda e: refresh_products()  # Сортировка в реальном времени
    )
    
    # Контейнер для карточек товаров
    products_container = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        spacing=10
    )
    
    def refresh_products():
        """Обновление списка товаров"""
        refresh_db = SessionLocal()
        try:
            search = search_field.value if search_field.visible and search_field.value else None
            # Проверяем, что выбрано не "Все поставщики"
            supplier_id = None
            if supplier_dropdown.visible and supplier_dropdown.value:
                value = supplier_dropdown.value.strip()
                # Проверяем, что это не пустая строка и не "Все поставщики"
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
            
            # Обрабатываем данные ДО закрытия соединения
            products_container.controls = []
            for product in products_list:
                try:
                    # Получаем данные связанных объектов пока соединение открыто
                    category_name = product.category.name if product.category else "Не указана"
                    manufacturer_name = product.manufacturer.name if product.manufacturer else "Не указан"
                    supplier_name = product.supplier.name if product.supplier else "Не указан"
                    
                    # Определяем цвет фона карточки
                    bg_color = "#FFFFFF"  # Основной фон
                    if product.discount_percent > 15:
                        bg_color = "#2E8B57"  # Скидка >15%
                    elif product.stock_quantity == 0:
                        bg_color = "#E0F7FA"  # Нет на складе (голубой)
                    
                    # Определяем цвет текста
                    text_color = "#000000" if bg_color == "#FFFFFF" or bg_color == "#E0F7FA" else "#FFFFFF"
                    
                    # Изображение товара с заглушкой
                    if product.image_path:
                        image_path = f"app/{product.image_path}"
                    else:
                        image_path = "app/static/images/picture.png"
                    
                    image_widget = ft.Container(
                        width=150,
                        height=150,
                        content=ft.Image(
                            src=image_path,
                            fit=ft.ImageFit.CONTAIN,
                            error_content=ft.Image(src="app/static/images/picture.png", fit=ft.ImageFit.CONTAIN)
                        ),
                        alignment=ft.alignment.center
                    )
                    
                    # Цена с учетом скидки
                    final_price = product.price * (1 - product.discount_percent / 100)
                    price_widget = ft.Column(
                        controls=[],
                        spacing=2
                    )
                    if product.discount_percent > 0:
                        # Старая цена перечеркнута красным
                        price_widget.controls.append(
                            ft.Text(
                                spans=[
                                    ft.TextSpan(
                                        f"{product.price:.2f} ₽",
                                        style=ft.TextStyle(
                                            decoration=ft.TextDecoration.LINE_THROUGH,
                                            color="#FF0000",
                                            size=14,
                                            font_family="Times New Roman"
                                        )
                                    )
                                ]
                            )
                        )
                        # Новая цена черным
                        price_widget.controls.append(
                            ft.Text(
                                f"{final_price:.2f} ₽",
                                size=16,
                                color=text_color,
                                weight=ft.FontWeight.BOLD,
                                font_family="Times New Roman"
                            )
                        )
                    else:
                        price_widget.controls.append(
                            ft.Text(
                                f"{product.price:.2f} ₽",
                                size=16,
                                color=text_color,
                                weight=ft.FontWeight.BOLD,
                                font_family="Times New Roman"
                            )
                        )
                    
                    # Действия для администратора
                    actions_row = ft.Row(controls=[], spacing=5)
                    if role == "admin":
                        actions_row.controls.append(
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Редактировать",
                                icon_color=text_color,
                                on_click=lambda e, p_id=product.id: edit_product(p_id)
                            )
                        )
                        actions_row.controls.append(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Удалить",
                                icon_color="#FF0000",
                                on_click=lambda e, p_id=product.id: delete_product_confirm(p_id)
                            )
                        )
                    
                    # Создаем карточку товара согласно макету
                    product_card = ft.Container(
                        content=ft.Row(
                            [
                                # Левая часть - фото
                                image_widget,
                                # Средняя часть - информация о товаре
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            # Заголовок: Категория | Наименование
                                            ft.Text(
                                                f"{category_name} | {product.name}",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                                color=text_color,
                                                font_family="Times New Roman"
                                            ),
                                            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                            ft.Text(f"Описание товара: {product.description or 'Нет описания'}", size=12, color=text_color, font_family="Times New Roman"),
                                            ft.Text(f"Производитель: {manufacturer_name}", size=12, color=text_color, font_family="Times New Roman"),
                                            ft.Text(f"Поставщик: {supplier_name}", size=12, color=text_color, font_family="Times New Roman"),
                                            price_widget,
                                            ft.Text(f"Единица измерения: {product.unit}", size=12, color=text_color, font_family="Times New Roman"),
                                            ft.Text(f"Количество на складе: {product.stock_quantity}", size=12, color=text_color, font_family="Times New Roman"),
                                            actions_row
                                        ],
                                        spacing=5,
                                        expand=True
                                    ),
                                    expand=True,
                                    padding=10
                                ),
                                # Правая часть - скидка
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                "Действующая скидка",
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=text_color,
                                                font_family="Times New Roman"
                                            ),
                                            ft.Text(
                                                f"{product.discount_percent:.1f}%",
                                                size=24,
                                                weight=ft.FontWeight.BOLD,
                                                color=text_color,
                                                font_family="Times New Roman"
                                            ) if product.discount_percent > 0 else ft.Text("0%", size=24, color=text_color, font_family="Times New Roman")
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        alignment=ft.MainAxisAlignment.CENTER
                                    ),
                                    width=150,
                                    padding=10
                                )
                            ],
                            spacing=10
                        ),
                        bgcolor=bg_color,
                        border=ft.border.all(1, "#CCCCCC"),
                        border_radius=5,
                        padding=10,
                        on_click=lambda e, p_id=product.id: edit_product(p_id) if role == "admin" else None,
                        data=product.id
                    )
                    
                    products_container.controls.append(product_card)
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
        global _open_form_dialog
        
        # Блокировка открытия более одного окна редактирования
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
            
            # Вычисление следующего ID при добавлении
            next_id = None
            if not product_id:
                from app.models import Product as ProductModel
                last_product = form_db.query(ProductModel).order_by(ProductModel.id.desc()).first()
                next_id = (last_product.id + 1) if last_product else 1
            
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
            
            # Поле ID товара (только для чтения, только при редактировании)
            id_field = None
            if product_id:
                id_field = ft.TextField(
                    label="ID товара",
                    value=str(product.id),
                    read_only=True,
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE
                )
            
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
            
            # Поле загрузки изображения
            image_file_picker = ft.FilePicker()
            page.overlay.append(image_file_picker)
            image_path_ref = [product.image_path if product else None]
            image_preview = ft.Container(
                width=300,
                height=200,
                content=ft.Image(
                    src=f"app/{product.image_path}" if product and product.image_path else "app/static/images/picture.png",
                    fit=ft.ImageFit.CONTAIN
                ),
                border=ft.border.all(1, "#CCCCCC"),
                border_radius=5
            )
            
            def on_image_picked(e: ft.FilePickerResultEvent):
                """Обработчик выбора изображения"""
                if e.files and len(e.files) > 0:
                    selected_file = e.files[0]
                    try:
                        # Сохраняем временный путь
                        image_path_ref[0] = selected_file.path
                        # Обновляем превью
                        image_preview.content = ft.Image(
                            src=selected_file.path,
                            fit=ft.ImageFit.CONTAIN
                        )
                        page.update()
                    except Exception as ex:
                        print(f"Ошибка при загрузке изображения: {ex}")
            
            image_file_picker.on_result = on_image_picked
            
            def pick_image(e):
                """Открытие диалога выбора изображения"""
                image_file_picker.pick_files(
                    allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp"],
                    dialog_title="Выберите изображение товара"
                )
            
            image_picker_button = ft.ElevatedButton(
                "Выбрать изображение",
                icon=ft.Icons.IMAGE,
                on_click=pick_image,
                bgcolor="#00FA9A",
                color="#000000"
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
                    
                    # Обработка изображения
                    saved_image_path = None
                    if image_path_ref[0]:
                        # Проверяем, является ли это новым файлом (выбранным через FilePicker)
                        # или существующим путем из базы данных
                        is_new_file = os.path.exists(image_path_ref[0]) and not image_path_ref[0].startswith("static/")
                        
                        if is_new_file:
                            # Новое изображение выбрано - обрабатываем его
                            try:
                                # Создаем директорию для изображений
                                upload_dir = "app/static/images/products"
                                os.makedirs(upload_dir, exist_ok=True)
                                
                                # Определяем ID для имени файла
                                target_id = product_id if product_id else next_id
                                
                                # Открываем и обрабатываем изображение
                                img = Image.open(image_path_ref[0])
                                # Изменяем размер до 300x200
                                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                                
                                # Сохраняем изображение
                                file_ext = os.path.splitext(image_path_ref[0])[1] or ".jpg"
                                filename = f"product_{target_id}{file_ext}"
                                filepath = os.path.join(upload_dir, filename)
                                img.save(filepath)
                                
                                saved_image_path = f"static/images/products/{filename}"
                                
                                # Удаляем старое изображение при редактировании
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
                            # При редактировании, если новое изображение не выбрано, оставляем старое
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
                    
                    # Удаляем все диалоги из overlay
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
                global _open_form_dialog
                _open_form_dialog = None
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
                                    color=ft.Colors.WHITE,
                                    font_family="Times New Roman"
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
                                    *([id_field] if id_field else []),
                                    name_field,
                                    description_field,
                                    category_dropdown,
                                    manufacturer_dropdown,
                                    supplier_form_dropdown,
                                    price_field,
                                    unit_field,
                                    stock_field,
                                    discount_field,
                                    ft.Divider(),
                                    ft.Text("Изображение товара:", size=14, weight=ft.FontWeight.BOLD, font_family="Times New Roman", color=ft.Colors.WHITE),
                                    image_preview,
                                    image_picker_button,
                                ],
                                scroll=ft.ScrollMode.AUTO,
                                spacing=10
                            ),
                            height=600,
                            width=500
                        ),
                        ft.Row(
                            [
                                ft.TextButton("Отмена", on_click=close_dialog, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                                ft.ElevatedButton("Сохранить", on_click=save_product, bgcolor="#00FA9A", color="#000000")
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
                        top=page.height / 2 - 300,
                    )
                ],
                width=page.width,
                height=page.height
            )
            
            # Сохраняем ссылку на открытый диалог
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
        """Обработчик поиска (оставлен для совместимости, но поиск уже в реальном времени)"""
        refresh_products()
    
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
    
    # Создание представления
    try:
        view = ft.View(
            route="/products",
        controls=[
            ft.AppBar(
                title=ft.Text("Список товаров", font_family="Times New Roman"),
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
                        on_click=lambda e: refresh_products(),
                        icon_color="#000000"
                    ),
                    ft.PopupMenuButton(
                        items=[
                            *([ft.PopupMenuItem(
                                text="Заказы",
                                icon=ft.Icons.SHOPPING_CART,
                                on_click=navigate_to_orders
                            )] if role in ["manager", "admin"] else []),
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
                                    f"Пользователь: {app_state.current_user.full_name if app_state.current_user else 'Гость'}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Times New Roman"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    search_field,
                                    supplier_dropdown,
                                    sort_dropdown,
                                    ft.ElevatedButton(
                                        "Добавить товар",
                                        icon=ft.Icons.ADD,
                                        on_click=add_product,
                                        visible=role == "admin",
                                        bgcolor="#00FA9A",  # Акцентирование внимания
                                        color="#000000"
                                    )
                                ],
                                wrap=True,
                                spacing=10
                            ),
                            bgcolor="#7FFF00",  # Дополнительный фон
                            padding=15,
                            border_radius=5,
                            visible=role in ["manager", "admin"]
                        ),
                        ft.Container(
                            content=products_container,
                            expand=True,
                            border=ft.border.all(1, "#CCCCCC"),
                            border_radius=5,
                            padding=10,
                            bgcolor="#FFFFFF"  # Основной фон
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

