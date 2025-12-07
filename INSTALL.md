# Инструкция по установке и запуску

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Инициализация базы данных

```bash
python migrations/init_db.py
```

Это создаст базу данных `shoe_store.db` и заполнит её начальными данными:
- Пользователи (admin, manager, client)
- Категории товаров
- Производители
- Поставщики

## Шаг 3: Создание заглушки изображения (опционально)

```bash
python create_image_placeholder.py
```

Это создаст файл `app/static/images/picture.png` - заглушку для товаров без изображения.

## Шаг 4: Импорт данных (если есть файлы в resources/import_data/)

```bash
python migrations/import_data.py
```

## Шаг 5: Запуск приложения

```bash
python run.py
```

Или:

```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

## Учетные записи для входа

- **Администратор**: login: `admin`, password: `admin123`
- **Менеджер**: login: `manager`, password: `manager123`
- **Клиент**: login: `client`, password: `client123`

## Структура базы данных

База данных SQLite создается автоматически при первом запуске. Файл БД: `shoe_store.db`

Для просмотра структуры БД используйте SQL скрипт: `migrations/create_db_script.sql`

