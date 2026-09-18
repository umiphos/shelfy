from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.product import ProductRequest
from ..services import product_service

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/{catalog_id}")
def get_products(catalog_id: int, db: Session = Depends(get_db)):
    return product_service.get_products(catalog_id, db)


@router.post("")
def create_product(data: ProductRequest, db: Session = Depends(get_db)):
    return product_service.create_product(data, db)


@router.get("/item/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product(product_id, db)


@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductRequest,
    db: Session = Depends(get_db),
):
    return product_service.update_product(product_id, data, db)


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product_service.delete_product(product_id, db)
    return {"message": "Producto eliminado"}
