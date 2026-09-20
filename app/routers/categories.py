from fastapi import APIRouter, Depends, HTTPException

from .. import models
from ..database import DbSession
from ..schemas.category import CategoryRequest
from ..security.auth0 import require_permission

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories(db: DbSession):
    return (
        db.query(models.Category)
        .filter(models.Category.active.is_(True))
        .order_by(models.Category.name)
        .all()
    )


@router.post("", dependencies=[Depends(require_permission("create:categories"))])
def create_category(data: CategoryRequest, db: DbSession):
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
