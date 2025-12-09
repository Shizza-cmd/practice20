"""
Создание администратора по умолчанию
"""
from app.database import SessionLocal
from app.models import User
from app.services.auth_service import get_password_hash

db = SessionLocal()

# Проверяем, есть ли уже администратор
admin = db.query(User).filter(User.role == "admin").first()
if admin:
    print(f"Администратор уже существует: {admin.login}")
else:
    # Создаём администратора по умолчанию
    admin = User(
        login="admin",
        password_hash=get_password_hash("admin"),
        full_name="Администратор",
        role="admin"
    )
    db.add(admin)
    db.commit()
    print("Создан администратор:")
    print("  Логин: admin")
    print("  Пароль: admin")

db.close()

