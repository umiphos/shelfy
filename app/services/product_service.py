from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..schemas.product import ProductRequest
from .image_service import delete_image_file

VALID_PRODUCT_STATUSES = {"available", "sold_out", "hidden"}


def _validate_product(data: ProductRequest, db: Session) -> None:
    if data.price <= 0:
        raise HTTPException(status_code=400, detail="El precio debe ser mayor que cero")
    if data.quantity <= 0:
        raise HTTPException(
            status_code=400, detail="La cantidad debe ser mayor que cero"
        )
    if data.status not in VALID_PRODUCT_STATUSES:
        raise HTTPException(status_code=400, detail="Estado de producto no válido")
    category = (
        db.query(models.Category)
        .filter(
            models.Category.id == data.category_id, models.Category.active.is_(True)
        )
        .first()
    )
    if not category:
        raise HTTPException(status_code=400, detail="Categoría no válida")


def get_products(catalog_id: int, db: Session) -> list[models.Product]:
    return (
        db.query(models.Product).filter(models.Product.catalog_id == catalog_id).all()
    )


def get_product(product_id: int, db: Session) -> models.Product:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def create_product(data: ProductRequest, db: Session) -> models.Product:
    if (
        not db.query(models.Catalog)
        .filter(models.Catalog.id == data.catalog_id)
        .first()
    ):
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    _validate_product(data, db)
    product = models.Product(**data.model_dump())
    product.name = product.name.strip()
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    product_id: int, data: ProductRequest, db: Session
) -> models.Product:
    product = get_product(product_id, db)
    _validate_product(data, db)
    for field, value in data.model_dump(exclude={"catalog_id"}).items():
        setattr(product, field, value)
    product.name = product.name.strip()
    db.commit()
    db.refresh(product)
    return product


def delete_product(product_id: int, db: Session) -> None:
    product = get_product(product_id, db)
    images = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .all()
    )
    for image in images:
        delete_image_file(image.filename)
        db.delete(image)
    db.delete(product)
    db.commit()
