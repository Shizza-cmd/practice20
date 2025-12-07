from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import User
from fastapi import HTTPException, status

# Используем pbkdf2_sha256 как основную схему (более надежная, без ограничений bcrypt)
# и bcrypt как резервную
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=29000
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    # Убеждаемся, что пароль - строка
    if not isinstance(password, str):
        password = str(password)
    
    # Хешируем пароль (pbkdf2_sha256 не имеет ограничения в 72 байта)
    return pwd_context.hash(password)


def authenticate_user(db: Session, login: str, password: str) -> User:
    """Аутентификация пользователя"""
    user = db.query(User).filter(User.login == login).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    return user


def get_user_by_login(db: Session, login: str) -> User | None:
    """Получение пользователя по логину"""
    return db.query(User).filter(User.login == login).first()

