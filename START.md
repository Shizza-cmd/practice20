# Последовательность запуска проекта

## Шаг 1: Установка зависимостей (если еще не установлены)
```bash
pip install -r requirements.txt
```

## Шаг 2: Инициализация базы данных
```bash
python migrations\init_db.py
```
Это создаст базу данных `shoe_store.db` и заполнит начальными данными.

## Шаг 3: Создание заглушки изображения (опционально)
```bash
python create_image_placeholder.py
```
Создаст файл `app/static/images/picture.png` для товаров без изображения.

## Шаг 4: Запуск приложения
```bash
python run.py
```
Или:
```bash
uvicorn app.main:app --reload
```

## Шаг 5: Открыть в браузере
http://localhost:8000

## Учетные записи для входа:
- **Администратор**: `admin` / `admin123`
- **Менеджер**: `manager` / `manager123`
- **Клиент**: `client` / `client123`

Или нажмите "Просмотр как гость" на странице входа.

