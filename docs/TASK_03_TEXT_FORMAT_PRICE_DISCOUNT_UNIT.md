# Задача 3: Привести цену, скидку и единицу измерения к текстовому формату как в ТЗ

## Описание задачи
Форматирование отображения:
- **Цена**: должна отображаться с указанием валюты и форматом (например, "1 500 руб." или "1500.00 ₽")
- **Скидка**: должна отображаться как "Скидка: 15%" или "Действующая скидка: 15%"
- **Единица измерения**: полное название (например, "штука" вместо "шт")

## Где нужно изменить

### 1. `desktop/products_view.py` — Отображение цены (строки 147-179)

**Текущее состояние:**
```python
# Цена с учетом скидки
final_price = product.price * (1 - product.discount_percent / 100)
price_row = ft.Row(controls=[], spacing=5)

if product.discount_percent > 0:
    price_row.controls.append(
        ft.Text(
            f"{product.price:.0f} руб.",  # <-- Простой формат
            size=12,
            color="#FF0000",
            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
            font_family="Times New Roman"
        )
    )
    price_row.controls.append(
        ft.Text(
            f"{final_price:.0f} руб.",  # <-- Простой формат
            ...
        )
    )
```

**Что нужно изменить:**
```python
def format_price(price: float) -> str:
    """Форматирование цены с разделителями тысяч"""
    return f"{price:,.0f}".replace(",", " ") + " руб."

# Использование:
price_row.controls.append(
    ft.Text(
        format_price(product.price),  # "1 500 руб."
        ...
    )
)
```

### 2. `desktop/products_view.py` — Отображение скидки (строки 228-260)

**Текущее состояние:**
```python
discount_block = ft.Container(
    content=ft.Column(
        [
            ft.Text(
                "Скидка",
                ...
            ),
            ft.Text(
                f"{product.discount_percent:.0f}%",
                ...
            )
        ],
        ...
    ),
    ...
)
```

**Что нужно изменить (если требуется по ТЗ):**
```python
# Если скидка = 0, показать "Нет скидки"
discount_text = f"{product.discount_percent:.0f}%" if product.discount_percent > 0 else "Нет"
discount_label = "Действующая скидка" if product.discount_percent > 0 else "Скидка"

discount_block = ft.Container(
    content=ft.Column(
        [
            ft.Text(
                discount_label,
                size=12,  # Уменьшить если длинный текст
                ...
            ),
            ft.Text(
                discount_text,
                ...
            )
        ],
        ...
    ),
    ...
)
```

### 3. `desktop/products_view.py` — Отображение единицы измерения (строки 211-216)

**Текущее состояние:**
```python
ft.Text(
    f"Ед. изм.: {product.unit}",  # "шт"
    ...
)
```

**Что нужно изменить:**
```python
# Словарь сокращений -> полных названий
UNIT_NAMES = {
    "шт": "штука",
    "шт.": "штука",
    "пар": "пара",
    "пара": "пара",
    "компл": "комплект",
    "компл.": "комплект",
    "м": "метр",
    "кг": "килограмм",
}

def get_full_unit_name(unit: str) -> str:
    """Получить полное название единицы измерения"""
    return UNIT_NAMES.get(unit.lower().strip(), unit)

# Использование:
ft.Text(
    f"Единица измерения: {get_full_unit_name(product.unit)}",
    ...
)
```

## Полный список изменений

| Файл | Строка | Текущее | Новое |
|------|--------|---------|-------|
| `products_view.py` | 154 | `f"{product.price:.0f} руб."` | `format_price(product.price)` |
| `products_view.py` | 162 | `f"{final_price:.0f} руб."` | `format_price(final_price)` |
| `products_view.py` | 172 | `f"{product.price:.0f} руб."` | `format_price(product.price)` |
| `products_view.py` | 212 | `f"Ед. изм.: {product.unit}"` | `f"Единица измерения: {get_full_unit_name(product.unit)}"` |
| `products_view.py` | 235 | `"Скидка"` | `"Действующая скидка"` (опционально) |

## Вспомогательные функции (добавить в начало файла)

```python
# Словарь единиц измерения
UNIT_FULL_NAMES = {
    "шт": "штука",
    "шт.": "штука", 
    "пар": "пара",
    "пара": "пара",
    "компл": "комплект",
    "компл.": "комплект",
}

def format_price(price: float) -> str:
    """Форматирование цены: 1500 -> '1 500 руб.'"""
    return f"{price:,.0f}".replace(",", " ") + " руб."

def get_full_unit_name(unit: str) -> str:
    """Получить полное название единицы измерения"""
    return UNIT_FULL_NAMES.get(unit.lower().strip(), unit)
```

## Зависимости

| Компонент | Зависит от | Влияет на |
|-----------|------------|-----------|
| `format_price()` | Нет (чистая функция) | Отображение цен |
| `get_full_unit_name()` | `UNIT_FULL_NAMES` | Отображение единиц |
| `UNIT_FULL_NAMES` | Нет | `get_full_unit_name()` |

## Почему это ничего не сломает

1. **Чистые функции**: `format_price()` и `get_full_unit_name()` не имеют побочных эффектов.

2. **Не изменяются данные**: Функции только форматируют вывод, не меняя значения в БД.

3. **Fallback в словаре**: Если единица измерения не найдена в словаре, возвращается исходное значение.

4. **Локализация изменений**: Все изменения в одном файле, в функции `refresh_products()`.

5. **Нет влияния на сохранение**: При сохранении товара используются оригинальные значения из полей формы.

## Тестирование

1. Открыть список товаров
2. Проверить формат цены: должно быть "1 500 руб." вместо "1500 руб."
3. Проверить формат скидки: "Действующая скидка: 15%"
4. Проверить единицу измерения: "Единица измерения: штука" вместо "Ед. изм.: шт"
5. Проверить товар без скидки: "Скидка: Нет" или "0%"
6. Сохранить товар и убедиться, что данные в БД не изменились

