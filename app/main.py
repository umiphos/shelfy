from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext

from . import models
from .database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CATÁLOGO API")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "CATÁLOGO API funcionando"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(models.User).filter(
        models.User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado",
        )

    user = models.User(
        email=data.email,
        password=pwd_context.hash(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Usuario creado",
        "id": user.id,
        "email": user.email,
    }


@app.get("/api/users")
def users(db: Session = Depends(get_db)):
    return db.query(models.User).all()