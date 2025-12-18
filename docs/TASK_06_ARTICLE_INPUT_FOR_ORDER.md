# Задача 6: Ввод артикула или выбор артикула вместо выбора товара при добавлении заказа

## Описание задачи
При добавлении товара в заказ заменить выпадающий список (`Dropdown`) с названиями товаров на:
1. **Текстовое поле для ввода артикула** — пользователь вводит артикул вручную
2. **Автодополнение** — при вводе показываются подходящие товары
3. **Или комбинированный вариант** — поле ввода + выпадающий список артикулов

## Где нужно изменить

### `desktop/orders_view.py` — Диалог добавления товара (строки 302-378)

**Текущее состояние:**
```python
def show_add_product_dialog(e):
    product_dropdown = ft.Dropdown(
        label="Товар",
        options=[ft.dropdown.Option(key=str(p.id), text=p.name) for p in products_list],
        # Показывает НАЗВАНИЕ товара, не артикул
        width=300,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color="#000000"
    )
```

**Что нужно изменить:**

## Вариант 1: Поле ввода артикула с поиском

```python
def show_add_product_dialog(e):
    # Контейнер для результатов поиска
    search_results = ft.Column(controls=[], spacing=2, scroll=ft.ScrollMode.AUTO)
    search_results_container = ft.Container(
        content=search_results,
        height=150,
        border=ft.border.all(1, "#CCCCCC"),
        visible=False
    )
    
    selected_product_ref = [None]  # Храним выбранный товар
    
    # Поле ввода артикула
    article_field = ft.TextField(
        label="Артикул товара",
        hint_text="Введите артикул или начните вводить для поиска",
        width=300,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color="#000000",
        on_change=lambda e: search_by_article(e.control.value)
    )
    
    # Отображение выбранного товара
    selected_product_text = ft.Text(
        "",
        size=12,
        color="#000000",
        font_family="Times New Roman"
    )
    
    def search_by_article(query: str):
        """Поиск товара по артикулу или названию"""
        search_results.controls.clear()
        
        if not query or len(query) < 1:
            search_results_container.visible = False
            page.update()
            return
        
        # Фильтрация товаров (артикул = id в данной системе)
        matches = [
            p for p in products_list 
            if str(p.id).startswith(query) or query.lower() in p.name.lower()
        ][:10]  # Ограничиваем 10 результатами
        
        if not matches:
            search_results.controls.append(
                ft.Text("Товары не найдены", size=11, color="#666666", italic=True)
            )
        else:
            for product in matches:
                search_results.controls.append(
                    ft.Container(
                        content=ft.Text(
                            f"[{product.id}] {product.name} - {product.price:.0f} руб.",
                            size=11,
                            color="#000000"
                        ),
                        padding=5,
                        on_click=lambda e, p=product: select_product(p),
                        ink=True,
                        bgcolor="#FFFFFF",
                        border=ft.border.only(bottom=ft.BorderSide(1, "#EEEEEE"))
                    )
                )
        
        search_results_container.visible = True
        page.update()
    
    def select_product(product):
        """Выбор товара из результатов поиска"""
        selected_product_ref[0] = product
        article_field.value = str(product.id)
        selected_product_text.value = f"Выбран: {product.name}"
        search_results_container.visible = False
        page.update()
    
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
        if selected_product_ref[0] and quantity_field.value:
            product = selected_product_ref[0]
            selected_products.append({
                'id': product.id,
                'name': product.name,
                'quantity': int(quantity_field.value)
            })
            refresh_order_items()
        elif article_field.value:
            # Попробовать найти по точному артикулу
            try:
                product_id = int(article_field.value)
                product = next((p for p in products_list if p.id == product_id), None)
                if product:
                    selected_products.append({
                        'id': product.id,
                        'name': product.name,
                        'quantity': int(quantity_field.value or 1)
                    })
                    refresh_order_items()
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Товар с таким артикулом не найден"),
                        bgcolor=ft.Colors.RED
                    )
                    page.snack_bar.open = True
            except ValueError:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Введите корректный артикул (число)"),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return
        
        add_product_dialog.open = False
        page.update()
    
    # ... остальной код диалога ...
    
    add_product_dialog = ft.AlertDialog(
        title=ft.Text("Добавить товар", color="#000000"),
        bgcolor="#00FF00",
        content=ft.Column(
            [
                article_field,
                search_results_container,
                selected_product_text,
                quantity_field
            ],
            spacing=10,
            tight=True,
            width=320
        ),
        actions=[
            ft.ElevatedButton("Отмена", on_click=close_add_dialog, ...),
            ft.ElevatedButton("Добавить", on_click=add_product_to_order, ...)
        ]
    )
```

## Вариант 2: Dropdown с артикулами вместо названий

Более простое изменение:

```python
product_dropdown = ft.Dropdown(
    label="Артикул товара",
    options=[
        ft.dropdown.Option(
            key=str(p.id), 
            text=f"[{p.id}] {p.name}"  # Показываем артикул + название
        ) 
        for p in products_list
    ],
    width=300,
    bgcolor="#FFFFFF",
    color="#000000",
    border_color="#000000"
)
```

## Вариант 3: Комбинированный (Dropdown + TextField)

```python
# Переключатель режима ввода
input_mode = ft.RadioGroup(
    content=ft.Row([
        ft.Radio(value="dropdown", label="Выбрать из списка"),
        ft.Radio(value="manual", label="Ввести артикул"),
    ]),
    value="dropdown",
    on_change=lambda e: toggle_input_mode(e.control.value)
)

product_dropdown = ft.Dropdown(
    label="Артикул товара",
    options=[ft.dropdown.Option(key=str(p.id), text=f"[{p.id}] {p.name}") for p in products_list],
    width=300,
    visible=True
)

article_manual_field = ft.TextField(
    label="Артикул (вручную)",
    width=300,
    visible=False
)

def toggle_input_mode(mode: str):
    product_dropdown.visible = (mode == "dropdown")
    article_manual_field.visible = (mode == "manual")
    page.update()
```

## Зависимости

| Компонент | Зависит от | Влияет на |
|-----------|------------|-----------|
| `article_field` | Нет | Поиск товара |
| `search_by_article()` | `products_list` | Результаты поиска |
| `select_product()` | `selected_product_ref` | Выбранный товар |
| `add_product_to_order()` | `selected_product_ref`, `quantity_field` | Добавление в заказ |

## Почему это ничего не сломает

1. **Изолированность**: Изменения только в диалоге добавления товара, не затрагивают сохранение заказа.

2. **Сохраняем структуру данных**: `selected_products` по-прежнему содержит `{id, name, quantity}`.

3. **Fallback**: Если поиск не работает, можно ввести артикул вручную.

4. **Валидация**: Проверяем существование товара перед добавлением.

5. **Обратная совместимость**: Вариант 2 (Dropdown с артикулами) — минимальное изменение.

## Рекомендация

Для минимальных рисков начать с **Варианта 2** (изменение формата в Dropdown):

```python
# Было:
options=[ft.dropdown.Option(key=str(p.id), text=p.name) for p in products_list]

# Стало:
options=[ft.dropdown.Option(key=str(p.id), text=f"[{p.id}] {p.name}") for p in products_list]
```

После тестирования можно перейти к **Варианту 1** с полем ввода и поиском.

## Тестирование

### Тест 1: Выбор из списка (Вариант 2)
1. Открыть форму заказа
2. Нажать "Добавить товар"
3. Убедиться, что в списке видны артикулы: `[1] Кроссовки Nike`
4. Выбрать товар
5. Нажать "Добавить"
6. **Ожидание**: Товар добавлен в заказ

### Тест 2: Ввод артикула (Вариант 1)
1. Открыть форму заказа
2. Нажать "Добавить товар"
3. Ввести артикул "5"
4. Убедиться, что появились результаты поиска
5. Выбрать товар из списка или нажать Enter
6. **Ожидание**: Товар найден и добавлен

### Тест 3: Несуществующий артикул
1. Ввести артикул "99999"
2. **Ожидание**: Сообщение "Товар с таким артикулом не найден"

### Тест 4: Некорректный ввод
1. Ввести "abc" в поле артикула
2. **Ожидание**: Сообщение "Введите корректный артикул (число)"

