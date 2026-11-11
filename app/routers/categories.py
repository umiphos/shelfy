from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas.category import CategoryRequest

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories(db: Session = Depends(get_db)):
    return (
        db.query(models.Category)
        .filter(models.Category.active.is_(True))
        .order_by(models.Category.name)
        .all()
    )


@router.post("")
def create_category(data: CategoryRequest, db: Session = Depends(get_db)):
    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=400, detail="El nombre de la categoría es obligatorio"
        )
    if db.query(models.Category).filter(models.Category.name == name).first():
        raise HTTPException(status_code=400, detail="La categoría ya existe")

    category = models.Category(name=name, active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
