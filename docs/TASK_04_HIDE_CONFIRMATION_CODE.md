# Задача 4: Скрыть код для подтверждения (только в БД, не показывать)

## Описание задачи
Код подтверждения заказа (`code`) должен храниться в базе данных, но **НЕ** отображаться в интерфейсе пользователя. Код используется только для идентификации заказа при получении.

## Где нужно изменить

### `desktop/orders_view.py` — Функция `refresh_orders()` (строки 93-98)

**Текущее состояние:**
```python
ft.Text(
    f"Код для получения: {order_data.code if order_data.code else order_data.id }",
    size=11,
    color="#000000",
    font_family="Times New Roman"
),
```

**Что нужно сделать:**
Удалить или закомментировать эти строки (93-98):

```python
# УДАЛИТЬ или ЗАКОММЕНТИРОВАТЬ:
# ft.Text(
#     f"Код для получения: {order_data.code if order_data.code else order_data.id }",
#     size=11,
#     color="#000000",
#     font_family="Times New Roman"
# ),
```

## Альтернативный вариант: Показывать только определённым ролям

Если код должен быть виден только администраторам:

```python
# В info_column, заменить строку с кодом на:
] + ([
    ft.Text(
        f"Код для получения: {order_data.code if order_data.code else order_data.id}",
        size=11,
        color="#000000",
        font_family="Times New Roman"
    )
] if role == "admin" else []),
```

Но это усложняет код. Лучше просто удалить строки.

## Что НЕ нужно менять

| Компонент | Изменять? | Причина |
|-----------|-----------|---------|
| `app/models.py` (Order.code) | ❌ НЕТ | Код должен храниться в БД |
| `app/schemas.py` (OrderResponse) | ❌ НЕТ | API может возвращать код для других систем |
| `app/services/order_service.py` | ❌ НЕТ | Генерация кода при создании заказа остаётся |

## Зависимости

| Компонент | Зависит от | Влияет на |
|-----------|------------|-----------|
| Отображение `code` | `Order.code` из БД | Только UI |
| `Order.code` в БД | Генерируется при создании | Сохраняется, но не показывается |
| API `/orders` | Может возвращать `code` | Не затронуто изменением UI |

## Почему это ничего не сломает

1. **Данные остаются в БД**: Поле `code` по-прежнему существует в модели `Order` и заполняется при создании заказа.

2. **API не затронуто**: Если есть REST API для заказов, оно продолжит возвращать `code`.

3. **Изолированность**: Удаляется только элемент UI (`ft.Text`), без изменения логики.

4. **Генерация кода работает**: В `order_service.py` код генерируется при создании заказа и сохраняется.

5. **Обратимость**: Можно легко вернуть отображение кода, раскомментировав строки.

## Проверка: Как генерируется код?

Посмотрим в `order_service.py`:

```python
def create_order(db: Session, order: OrderCreate) -> Order:
    db_order = Order(
        article=order.article,
        status=order.status,
        pickup_address=order.pickup_address,
        order_date=order.order_date,
        delivery_date=order.delivery_date
        # code не указан явно - значит генерируется автоматически или в другом месте
    )
```

**Важно**: Нужно проверить, как генерируется `code`. Если он не генерируется автоматически, возможно нужно добавить генерацию:

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
        code=generate_order_code()  # <-- Добавить генерацию
    )
```

## Тестирование

1. Открыть список заказов
2. Убедиться, что код для получения **НЕ** отображается
3. Проверить в БД (через SQLite браузер), что поле `code` заполнено
4. Создать новый заказ
5. Убедиться, что в БД для нового заказа есть `code`
6. Убедиться, что в UI код не показывается

## Команда для проверки БД

```sql
SELECT id, article, code FROM orders ORDER BY id DESC LIMIT 5;
```

Должны увидеть заполненные значения в колонке `code`.

