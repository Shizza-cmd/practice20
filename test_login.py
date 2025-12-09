from app.services.auth_service import authenticate_user
from app.database import SessionLocal

db = SessionLocal()

# Тестируем вход с данными из Excel
test_users = [
    ("94d5ous@gmail.com", "uzWC67"),
    ("admin", "admin"),
    ("uth4iz@mail.com", "2L6KZG"),
]

for login, password in test_users:
    user = authenticate_user(db, login, password)
    if user:
        print(f"✓ {login} - УСПЕШНО ({user.full_name}, {user.role})")
    else:
        print(f"✗ {login} - ОШИБКА")

db.close()

