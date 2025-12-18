# Задача 2: Подсветка синим строки, если остаток на складе = 0

## Описание задачи
Карточки товаров с нулевым остатком на складе (`stock_quantity == 0`) должны визуально выделяться синим цветом фона.

## Где нужно изменить

### `desktop/products_view.py` — Функция `refresh_products()` (строки 262-284)

**Текущее состояние (строка 263-282):**
```python
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
    bgcolor="#FFFFFF",  # <-- Всегда белый
    border=ft.border.all(2, "#000000"),
    padding=5,
    on_click=lambda e, p_id=product.id: edit_product(p_id) if role == "admin" else None,
    data=product.id
)
```

**Что нужно изменить:**
Добавить условную логику для цвета фона:

```python
# Определяем цвет фона: синий если остаток 0, иначе белый
card_bgcolor = "#90CAF9" if product.stock_quantity == 0 else "#FFFFFF"

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
    bgcolor=card_bgcolor,  # <-- Условный цвет
    border=ft.border.all(2, "#000000"),
    padding=5,
    on_click=lambda e, p_id=product.id: edit_product(p_id) if role == "admin" else None,
    data=product.id
)
```

## Точное место изменения

**Файл:** `desktop/products_view.py`  
**Строка:** 277  
**Изменение:** Заменить `bgcolor="#FFFFFF"` на `bgcolor=card_bgcolor`

**Добавить перед строкой 263:**
```python
# Цвет фона: синий если остаток 0
card_bgcolor = "#90CAF9" if product.stock_quantity == 0 else "#FFFFFF"
```

## Зависимости

| Компонент | Зависит от | Влияет на |
|-----------|------------|-----------|
| `card_bgcolor` | `product.stock_quantity` | `product_card.bgcolor` |
| `product.stock_quantity` | БД (таблица `products`) | Визуальное отображение |

## Почему это ничего не сломает

1. **Минимальность изменений**: Добавляется только одна переменная и изменяется один параметр.

2. **Нет изменений в структуре данных**: Мы только читаем существующее поле `stock_quantity`, которое уже загружается из БД.

3. **Нет влияния на функциональность**: Изменение чисто визуальное, не затрагивает клики, фильтрацию, редактирование.

4. **Обратимость**: При необходимости можно легко откатить, заменив `card_bgcolor` обратно на `"#FFFFFF"`.

5. **Изолированность**: Изменение находится внутри цикла `for product in products_list:` и не влияет на другие товары.

## Альтернативные цвета

Если синий `#90CAF9` не подходит, можно использовать:
- `#BBDEFB` — более светлый синий
- `#64B5F6` — более насыщенный синий
- `#42A5F5` — ещё более насыщенный
- `#2196F3` — Material Blue 500

## Тестирование

1. Создать или найти товар с `stock_quantity = 0`
2. Открыть список товаров
3. Убедиться, что карточка этого товара имеет синий фон
4. Изменить остаток на > 0
5. Обновить список — карточка должна стать белой
6. Проверить сортировку "По возрастанию остатка" — синие карточки должны быть сверху

