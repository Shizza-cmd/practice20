"""
Модуль импорта данных для десктопного приложения
"""
import flet as ft
import os
import sys

# Добавление корневой директории проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, Category, Manufacturer, Supplier, Product, Order
from app.services.auth_service import get_password_hash
from datetime import datetime
import pandas as pd


def create_import_view(page: ft.Page, app_state):
    """Создание экрана импорта данных"""
    
    role = app_state.current_user.role if app_state.current_user else "guest"
    
    # Проверка прав доступа
    if role != "admin":
        from desktop.products_view import create_products_view
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Доступ запрещен. Только для администратора."),
            bgcolor=ft.Colors.RED
        )
        page.snack_bar.open = True
        page.update()
        return create_products_view(page, app_state)
    
    status_text = ft.Text(
        value="Готов к импорту",
        size=14,
        font_family="Times New Roman"
    )
    
    def import_users(e):
        """Импорт пользователей"""
        db = SessionLocal()
        try:
            status_text.value = "Импорт пользователей..."
            page.update()
            
            users_file = os.path.join("pril", "user_import.xlsx")
            if not os.path.exists(users_file):
                status_text.value = f"Ошибка: файл {users_file} не найден"
                status_text.color = ft.Colors.RED
                page.update()
                return
            
            try:
                df = pd.read_excel(users_file)
                print(f"Найдено {len(df)} строк в файле пользователей")
                print(f"Колонки в файле: {df.columns.tolist()}")
                imported_count = 0
                
                for idx, row in df.iterrows():
                    try:
                        login = str(row.get('Логин', '')).strip()
                        password = str(row.get('Пароль', '')).strip()
                        full_name = str(row.get('ФИО', '')).strip()
                        # Обработка роли из поля "Роль сотрудника"
                        role_str = str(row.get('Роль сотрудника', row.get('Роль', 'client'))).strip().lower()
                        
                        print(f"Строка {idx}: Логин='{login}', ФИО='{full_name}', Роль='{role_str}'")
                        
                        # Преобразование ролей
                        if 'администратор' in role_str or 'admin' in role_str:
                            role = 'admin'
                        elif 'менеджер' in role_str or 'manager' in role_str:
                            role = 'manager'
                        else:
                            role = 'client'
                        
                        if not login or not password:
                            print(f"  Пропущено: нет логина или пароля")
                            continue
                        
                        existing_user = db.query(User).filter(User.login == login).first()
                        if existing_user:
                            print(f"  Пользователь {login} уже существует")
                        else:
                            user = User(
                                login=login,
                                password_hash=get_password_hash(password),
                                full_name=full_name,
                                role=role
                            )
                            db.add(user)
                            imported_count += 1
                            print(f"  Добавлен пользователь {login} с ролью {role}")
                    except Exception as ex:
                        print(f"Ошибка при импорте пользователя (строка {idx}): {ex}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                db.commit()
                status_text.value = f"Импортировано пользователей: {imported_count}"
                status_text.color = ft.Colors.GREEN
            except Exception as ex:
                db.rollback()
                status_text.value = f"Ошибка импорта пользователей: {str(ex)}"
                status_text.color = ft.Colors.RED
                import traceback
                traceback.print_exc()
            
            page.update()
        except Exception as ex:
            status_text.value = f"Ошибка: {str(ex)}"
            status_text.color = ft.Colors.RED
            page.update()
        finally:
            db.close()
    
    def import_products(e):
        """Импорт товаров"""
        db = SessionLocal()
        try:
            status_text.value = "Импорт товаров..."
            page.update()
            
            products_file = os.path.join("pril", "Tovar.xlsx")
            if not os.path.exists(products_file):
                status_text.value = f"Ошибка: файл {products_file} не найден"
                status_text.color = ft.Colors.RED
                page.update()
                return
            
            try:
                df = pd.read_excel(products_file)
                imported_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # Получение или создание категории
                        # Используем поле "Категория товара" (Женская обувь, Мужская обувь)
                        category_name = str(row.get('Категория товара', row.get('Категория', ''))).strip()
                        if not category_name:
                            continue
                        category = db.query(Category).filter(Category.name == category_name).first()
                        if not category:
                            category = Category(name=category_name)
                            db.add(category)
                            db.flush()
                        
                        # Получение или создание производителя
                        manufacturer_name = str(row.get('Производитель', '')).strip()
                        if not manufacturer_name:
                            continue
                        manufacturer = db.query(Manufacturer).filter(Manufacturer.name == manufacturer_name).first()
                        if not manufacturer:
                            manufacturer = Manufacturer(name=manufacturer_name)
                            db.add(manufacturer)
                            db.flush()
                        
                        # Получение или создание поставщика
                        supplier_name = str(row.get('Поставщик', '')).strip()
                        if not supplier_name:
                            continue
                        supplier = db.query(Supplier).filter(Supplier.name == supplier_name).first()
                        if not supplier:
                            supplier = Supplier(name=supplier_name)
                            db.add(supplier)
                            db.flush()
                        
                        # Создание товара
                        # Обработка цены
                        price_val = row.get('Цена', 0)
                        try:
                            if pd.isna(price_val):
                                price_val = 0
                            else:
                                price_val = float(price_val)
                        except:
                            price_val = 0
                        
                        # Обработка количества
                        stock_val = row.get('Кол-во на складе', row.get('Количество на складе', 0))
                        try:
                            if pd.isna(stock_val):
                                stock_val = 0
                            else:
                                stock_val = int(float(stock_val))  # Сначала float, потом int для обработки "0.0"
                        except:
                            stock_val = 0
                        
                        # Обработка скидки
                        discount_val = row.get('Действующая скидка', row.get('Скидка', 0))
                        try:
                            if pd.isna(discount_val):
                                discount_val = 0
                            else:
                                discount_val = float(discount_val)
                        except:
                            discount_val = 0
                        
                        product = Product(
                            name=str(row.get('Наименование товара', row.get('Наименование', ''))).strip(),
                            category_id=category.id,
                            description=str(row.get('Описание товара', row.get('Описание', ''))).strip() or None,
                            manufacturer_id=manufacturer.id,
                            supplier_id=supplier.id,
                            price=price_val,
                            unit=str(row.get('Единица измерения', 'шт')).strip() or 'шт',
                            stock_quantity=stock_val,
                            discount_percent=discount_val
                        )
                        
                        # Обработка изображения
                        image_num = str(row.get('Фото', '')).strip()
                        if image_num:
                            # Убираем расширение если есть
                            image_num = image_num.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
                            if image_num.isdigit():
                                image_path = f"static/images/products/{image_num}.jpg"
                                if os.path.exists(f"pril/{image_num}.jpg"):
                                    # Копируем изображение
                                    import shutil
                                    os.makedirs("app/static/images/products", exist_ok=True)
                                    shutil.copy(f"pril/{image_num}.jpg", f"app/{image_path}")
                                product.image_path = image_path
                        
                        db.add(product)
                        imported_count += 1
                    except Exception as ex:
                        print(f"Ошибка при импорте товара: {ex}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                db.commit()
                status_text.value = f"Импортировано товаров: {imported_count}. Обновите список товаров."
                status_text.color = ft.Colors.GREEN
            except Exception as ex:
                db.rollback()
                status_text.value = f"Ошибка импорта товаров: {str(ex)}"
                status_text.color = ft.Colors.RED
                import traceback
                traceback.print_exc()
            
            page.update()
        except Exception as ex:
            status_text.value = f"Ошибка: {str(ex)}"
            status_text.color = ft.Colors.RED
            page.update()
        finally:
            db.close()
    
    def import_orders(e):
        """Импорт заказов"""
        db = SessionLocal()
        try:
            status_text.value = "Импорт заказов..."
            page.update()
            
            orders_file = os.path.join("pril", "Заказ_import.xlsx")
            if not os.path.exists(orders_file):
                status_text.value = f"Ошибка: файл {orders_file} не найден"
                status_text.color = ft.Colors.RED
                page.update()
                return
            
            # Загружаем адреса пунктов выдачи
            pickup_points_file = os.path.join("pril", "Пункты выдачи_import.xlsx")
            pickup_points = []
            if os.path.exists(pickup_points_file):
                pickup_df = pd.read_excel(pickup_points_file)
                # Адреса в первой колонке, индекс соответствует номеру
                pickup_points = pickup_df.iloc[:, 0].tolist()
                print(f"Загружено {len(pickup_points)} пунктов выдачи")
            
            try:
                df = pd.read_excel(orders_file)
                imported_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # Используем поле "Артикул заказа" или "Артикул"
                        article = str(row.get('Артикул заказа', row.get('Артикул', ''))).strip()
                        status = str(row.get('Статус заказа', row.get('Статус', 'новый'))).strip().lower()
                        # Преобразуем статус
                        if 'завершен' in status or 'выполнен' in status:
                            status = 'выполнен'
                        elif 'новый' in status:
                            status = 'новый'
                        elif 'обработке' in status:
                            status = 'в обработке'
                        elif 'отменен' in status:
                            status = 'отменен'
                        else:
                            status = 'новый'
                        
                        # Адрес пункта выдачи - может быть номером или полным адресом
                        pickup_address_raw = str(row.get('Адрес пункта выдачи', '')).strip()
                        # Если это число, получаем полный адрес из списка пунктов выдачи
                        if pickup_address_raw.isdigit():
                            pickup_index = int(pickup_address_raw) - 1  # Нумерация с 1
                            if 0 <= pickup_index < len(pickup_points):
                                pickup_address = pickup_points[pickup_index]
                            else:
                                pickup_address = f"Пункт выдачи #{pickup_address_raw}"
                        else:
                            pickup_address = pickup_address_raw
                        
                        # Обработка даты заказа
                        order_date_str = row.get('Дата заказа', '')
                        if pd.isna(order_date_str):
                            order_date = datetime.now()
                        elif isinstance(order_date_str, str):
                            # Пробуем разные форматы дат
                            for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']:
                                try:
                                    order_date = datetime.strptime(order_date_str, fmt)
                                    break
                                except:
                                    continue
                            else:
                                order_date = datetime.now()
                        else:
                            order_date = order_date_str if isinstance(order_date_str, datetime) else datetime.now()
                        
                        # Обработка даты доставки
                        delivery_date_str = row.get('Дата доставки', '')
                        delivery_date = None
                        if not pd.isna(delivery_date_str):
                            if isinstance(delivery_date_str, str):
                                # Пробуем разные форматы дат
                                for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']:
                                    try:
                                        delivery_date = datetime.strptime(delivery_date_str, fmt)
                                        break
                                    except:
                                        continue
                            elif isinstance(delivery_date_str, datetime):
                                delivery_date = delivery_date_str
                        
                        if not article:
                            continue
                        
                        # Артикул заказа не уникален - разные заказы могут содержать одинаковые товары
                        order = Order(
                            article=article,
                            status=status,
                            pickup_address=pickup_address,
                            order_date=order_date,
                            delivery_date=delivery_date
                        )
                        db.add(order)
                        imported_count += 1
                    except Exception as ex:
                        print(f"Ошибка при импорте заказа: {ex}")
                        continue
                
                db.commit()
                status_text.value = f"Импортировано заказов: {imported_count}. Обновите список заказов."
                status_text.color = ft.Colors.GREEN
            except Exception as ex:
                db.rollback()
                status_text.value = f"Ошибка импорта заказов: {str(ex)}"
                status_text.color = ft.Colors.RED
                import traceback
                traceback.print_exc()
            
            page.update()
        except Exception as ex:
            status_text.value = f"Ошибка: {str(ex)}"
            status_text.color = ft.Colors.RED
            page.update()
        finally:
            db.close()
    
    def import_all(e):
        """Импорт всех данных"""
        import_users(e)
        import_products(e)
        import_orders(e)
        status_text.value = "Импорт всех данных завершен"
        status_text.color = ft.Colors.GREEN
        page.update()
    
    def on_back(e):
        """Обработчик кнопки Назад"""
        from desktop.products_view import create_products_view
        page.views.clear()
        page.views.append(create_products_view(page, app_state))
        page.update()
    
    def on_logout(e):
        """Выход из системы"""
        from desktop.auth_view import create_login_view
        app_state.logout()
        page.views.clear()
        page.views.append(create_login_view(page, app_state))
        page.update()
    
    view = ft.View(
        route="/import",
        controls=[
            ft.AppBar(
                title=ft.Text("Импорт данных", font_family="Times New Roman"),
                bgcolor="#00FA9A",  # Акцентирование внимания
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Назад",
                        on_click=on_back,
                        icon_color="#000000"
                    ),
                    ft.PopupMenuButton(
                        items=[
                            ft.PopupMenuItem(
                                text="Товары",
                                icon=ft.Icons.INVENTORY,
                                on_click=lambda e: on_back(e)
                            ),
                            ft.PopupMenuItem(
                                text="Заказы",
                                icon=ft.Icons.SHOPPING_CART,
                                on_click=lambda e: (
                                    page.views.clear(),
                                    page.views.append(
                                        __import__("desktop.orders_view", fromlist=["create_orders_view"]).create_orders_view(page, app_state)
                                    ),
                                    page.update()
                                ) if app_state.current_user.role in ["manager", "admin"] else None
                            ),
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
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "Импорт данных из Excel файлов",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        font_family="Times New Roman"
                                    ),
                                    ft.Divider(height=20),
                                    ft.Text(
                                        "Файлы должны находиться в папке pril/:",
                                        size=14,
                                        font_family="Times New Roman"
                                    ),
                                    ft.Text(
                                        "• user_import.xlsx - пользователи",
                                        size=12,
                                        font_family="Times New Roman"
                                    ),
                                    ft.Text(
                                        "• Tovar.xlsx - товары",
                                        size=12,
                                        font_family="Times New Roman"
                                    ),
                                    ft.Text(
                                        "• Заказ_import.xlsx - заказы",
                                        size=12,
                                        font_family="Times New Roman"
                                    ),
                                    ft.Divider(height=20),
                                    ft.Row(
                                        [
                                            ft.ElevatedButton(
                                                "Импорт пользователей",
                                                icon=ft.Icons.PEOPLE,
                                                on_click=import_users,
                                                bgcolor="#00FA9A",
                                                color="#000000"
                                            ),
                                            ft.ElevatedButton(
                                                "Импорт товаров",
                                                icon=ft.Icons.INVENTORY,
                                                on_click=import_products,
                                                bgcolor="#00FA9A",
                                                color="#000000"
                                            ),
                                            ft.ElevatedButton(
                                                "Импорт заказов",
                                                icon=ft.Icons.SHOPPING_CART,
                                                on_click=import_orders,
                                                bgcolor="#00FA9A",
                                                color="#000000"
                                            ),
                                            ft.ElevatedButton(
                                                "Импорт всех данных",
                                                icon=ft.Icons.UPLOAD,
                                                on_click=import_all,
                                                bgcolor="#7FFF00",
                                                color="#000000"
                                            )
                                        ],
                                        wrap=True,
                                        spacing=10
                                    ),
                                    ft.Divider(height=20),
                                    status_text
                                ],
                                spacing=10
                            ),
                            padding=20,
                            bgcolor="#FFFFFF",
                            border=ft.border.all(1, "#CCCCCC"),
                            border_radius=5
                        )
                    ],
                    expand=True,
                    spacing=10
                ),
                padding=20,
                expand=True,
                bgcolor="#FFFFFF"
            )
        ]
    )
    
    return view

