import bcrypt

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine


Base.metadata.create_all(bind=engine)


app = FastAPI(title="CATÁLOGO API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CatalogRequest(BaseModel):
    name: str
    user_id: int


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "CATÁLOGO API funcionando"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/api/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado",
        )

    hashed_password = bcrypt.hashpw(
        data.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    user = models.User(
        email=data.email,
        password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Usuario creado",
        "id": user.id,
        "email": user.email,
    }


@app.post("/api/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    password_valid = bcrypt.checkpw(
        data.password.encode("utf-8"),
        user.password.encode("utf-8"),
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    return {
        "message": "Login correcto",
        "id": user.id,
        "email": user.email,
    }


@app.get("/api/catalogs/{user_id}")
def get_catalog(
    user_id: int,
    db: Session = Depends(get_db),
):
    catalog = (
        db.query(models.Catalog)
        .filter(models.Catalog.user_id == user_id)
        .first()
    )

    if not catalog:
        return None

    return {
        "id": catalog.id,
        "name": catalog.name,
        "user_id": catalog.user_id,
    }


@app.post("/api/catalogs")
def create_catalog(
    data: CatalogRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.id == data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    existing_catalog = (
        db.query(models.Catalog)
        .filter(models.Catalog.user_id == data.user_id)
        .first()
    )

    if existing_catalog:
        raise HTTPException(
            status_code=400,
            detail="El usuario ya tiene un catálogo",
        )

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="El nombre del catálogo es obligatorio",
        )

    catalog = models.Catalog(
        name=name,
        user_id=data.user_id,
    )

    db.add(catalog)
    db.commit()
    db.refresh(catalog)

    return {
        "id": catalog.id,
        "name": catalog.name,
        "user_id": catalog.user_id,
    }