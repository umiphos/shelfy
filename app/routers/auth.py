from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import LoginRequest, RegisterRequest
from ..services import auth_service

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register_user(data, db)
    return {"message": "Usuario creado", "id": user.id, "email": user.email}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(data, db)
    return {"message": "Login correcto", "id": user.id, "email": user.email}
