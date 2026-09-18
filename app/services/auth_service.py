import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..schemas.auth import LoginRequest, RegisterRequest


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def register_user(data: RegisterRequest, db: Session) -> models.User:
    existing_user = (
        db.query(models.User).filter(models.User.email == data.email).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    user = models.User(email=data.email, password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(data: LoginRequest, db: Session) -> models.User:
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return user
