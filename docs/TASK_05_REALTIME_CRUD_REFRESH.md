# Задача 5: Тестирование добавления, удаления, редактирования записей (мгновенное отображение)

## Описание задачи
Новые/изменённые/удалённые записи должны **сразу** появляться в списке без необходимости перезапуска приложения или ручного обновления.

**Проблема**: На ноутбуке Кострыкина новые заказы не появлялись.

## Возможные причины проблемы

### 1. Не вызывается `refresh_orders()` после сохранения

**Файл**: `desktop/orders_view.py`, функция `save_order()` (строки 383-460)

**Проверить строку 438:**
```python
refresh_orders()  # <-- Должен вызываться после успешного сохранения
```

### 2. Сессия БД не коммитится или не закрывается

**Файл**: `app/services/order_service.py`, функция `create_order()` (строки 17-41)

**Текущее состояние:**
```python
def create_order(db: Session, order: OrderCreate) -> Order:
    db_order = Order(...)
    db.add(db_order)
    db.flush()
    # ... добавление items
    db.commit()  # <-- Коммит есть
    db.refresh(db_order)
    return db_order
```

### 3. Используется старая сессия БД для чтения

**Файл**: `desktop/orders_view.py`, функция `refresh_orders()` (строки 39-61)

**Текущее состояние:**
```python
def refresh_orders():
    refresh_db = SessionLocal()  # <-- Создаётся НОВАЯ сессия
    try:
        orders_list = get_orders(refresh_db)
        # ...
    finally:
        refresh_db.close()  # <-- Закрывается
```

Это правильно! Новая сессия гарантирует свежие данные.

### 4. Проблема с `page.update()` после сохранения

**Проверить в `save_order()`:**
```python
refresh_orders()
page.update()  # <-- Должен вызываться ПОСЛЕ refresh_orders()
```

## Детальный анализ проблемы

### Возможная причина: Заказ создаётся без `code`

В модели `Order`:
```python
code = Column(String(10), nullable=False)  # <-- nullable=False!
```

Но в `create_order()`:
```python
db_order = Order(
    article=order.article,
    status=order.status,
    pickup_address=order.pickup_address,
    order_date=order.order_date,
    delivery_date=order.delivery_date
    # code НЕ УКАЗАН!
)
```

**Это может вызывать ошибку при коммите!**

## Исправление: Генерация кода заказа

**Файл**: `app/services/order_service.py`

```python
import random
import string

def generate_order_code() -> str:
    """Генерация 6-значного кода заказа"""
    return ''.join(random.choices(string.digits, k=6))

def create_order(db: Session, order: OrderCreate) -> Order:
    db_order = Order(
        article=order.article,
        status=order.status,
        pickup_address=order.pickup_address,
        order_date=order.order_date,
        delivery_date=order.delivery_date,
        code=generate_order_code()  # <-- ДОБАВИТЬ!
    )
    db.add(db_order)
    db.flush()
    # ...
```

## Полный чек-лист исправлений

### 1. `app/services/order_service.py` — Добавить генерацию кода

```python
import random
import string

def generate_order_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

# В create_order() добавить:
code=generate_order_code()
```

### 2. `desktop/orders_view.py` — Убедиться в правильном порядке вызовов

```python
def save_order(e):
    save_db = SessionLocal()
    try:
        # ... валидация и создание/обновление ...
        
        # ВАЖНО: Закрыть диалог ДО refresh
        if dialog_stack_ref[0] and dialog_stack_ref[0] in page.overlay:
            page.overlay.remove(dialog_stack_ref[0])
        
        # Показать уведомление
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Заказ сохранен"),
            bgcolor=ft.Colors.GREEN
        )
        page.snack_bar.open = True
        
        # Обновить список
        refresh_orders()
        
        # Обновить страницу
        page.update()
        
    except Exception as ex:
        # ...
    finally:
        save_db.close()  # <-- ОБЯЗАТЕЛЬНО закрыть сессию
```

### 3. `desktop/orders_view.py` — Проверить `refresh_orders()`

```python
def refresh_orders():
    refresh_db = SessionLocal()
    try:
        orders_list = get_orders(refresh_db)
        orders_container.controls.clear()
        
        if not orders_list:
            # ... показать "Заказы не найдены"
            page.update()
            return
        
        for order in orders_list:
            card = create_order_card(order)
            orders_container.controls.append(card)
        
        page.update()  # <-- ОБЯЗАТЕЛЬНО вызвать
        
    except Exception as e:
        print(f"Ошибка при обновлении заказов: {e}")
        import traceback
        traceback.print_exc()  # <-- Для отладки
    finally:
        refresh_db.close()
```

## Зависимости

| Компонент | Зависит от | Влияет на |
|-----------|------------|-----------|
| `create_order()` | `Order.code` (обязательное поле) | Создание заказа |
| `refresh_orders()` | `get_orders()`, `SessionLocal()` | Отображение списка |
| `page.update()` | Flet framework | Перерисовка UI |
| `save_db.close()` | SQLAlchemy session | Освобождение ресурсов |

## Почему это ничего не сломает

1. **Генерация кода**: Добавляем обязательное поле, которое раньше отсутствовало (могло вызывать ошибки).

2. **Порядок вызовов**: Правильный порядок (close dialog → refresh → update) не меняет логику, только гарантирует корректное отображение.

3. **Закрытие сессий**: `finally: save_db.close()` гарантирует освобождение ресурсов даже при ошибках.

4. **Traceback**: Добавление `traceback.print_exc()` помогает в отладке, не влияет на работу.

## Тестирование

### Тест 1: Создание заказа
1. Открыть список заказов
2. Нажать "Добавить заказ"
3. Заполнить форму
4. Нажать "Сохранить"
5. **Ожидание**: Новый заказ появляется в списке БЕЗ перезагрузки

### Тест 2: Редактирование заказа
1. Кликнуть на существующий заказ (admin)
2. Изменить статус или адрес
3. Нажать "Сохранить"
4. **Ожидание**: Изменения видны сразу

### Тест 3: Удаление заказа
1. Открыть заказ
2. Нажать "Удалить"
3. Подтвердить удаление
4. **Ожидание**: Заказ исчезает из списка

### Тест 4: Проверка на другом устройстве
1. Открыть приложение на втором устройстве
2. На первом создать заказ
3. На втором обновить список (выйти и войти обратно в раздел заказов)
4. **Ожидание**: Новый заказ виден

## Отладка

Добавить логирование в `save_order()`:

```python
def save_order(e):
    print("=== Начало сохранения заказа ===")
    save_db = SessionLocal()
    try:
        # ...
        result = create_order(save_db, order_data)
        print(f"Заказ создан: id={result.id}, article={result.article}")
        
        refresh_orders()
        print("refresh_orders() выполнен")
        
        page.update()
        print("page.update() выполнен")
        
    except Exception as ex:
        print(f"ОШИБКА: {ex}")
        import traceback
        traceback.print_exc()
    finally:
        save_db.close()
        print("=== Сохранение завершено ===")
```

