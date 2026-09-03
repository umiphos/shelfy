from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import Base, engine

from . import models

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


@app.get("/")
def root():
    return {"message": "CATÁLOGO API funcionando"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/register")
def register(data: RegisterRequest):
    return {
        "message": "Registro recibido",
        "email": data.email,
    }