from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models
from ..core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGES_PER_PRODUCT = 5


def _require_owned_product(
    product_id: int,
    user: models.User,
    db: Session,
) -> models.Product:
    product = (
        db.query(models.Product)
        .join(models.Catalog, models.Product.catalog_id == models.Catalog.id)
        .filter(
            models.Product.id == product_id,
            models.Catalog.user_id == user.id,
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def _require_public_product(product_id: int, db: Session) -> models.Product:
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id,
            models.Product.status != "hidden",
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def delete_image_file(filename: str) -> None:
    filepath = settings.product_upload_dir / filename
    if filepath.exists():
        filepath.unlink()


async def save_product_image(
    product_id: int,
    file: UploadFile,
    user: models.User,
    db: Session,
) -> models.ProductImage:
    _require_owned_product(product_id, user, db)

    image_count = (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .count()
    )
    if image_count >= MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=400, detail="El producto permite máximo 5 imágenes"
        )
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Formato de imagen no permitido")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 2 MB")

    extension = Path(file.filename or "").suffix.lower()
    filename = f"{product_id}_{image_count + 1}{extension}"
    settings.product_upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.product_upload_dir / filename).write_bytes(contents)

    image = models.ProductImage(
        product_id=product_id,
        filename=filename,
        position=image_count,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_product_image(image_id: int, user: models.User, db: Session) -> None:
    image = (
        db.query(models.ProductImage).filter(models.ProductImage.id == image_id).first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    _require_owned_product(image.product_id, user, db)
    delete_image_file(image.filename)
    db.delete(image)
    db.commit()


def _get_product_images(product_id: int, db: Session) -> list[models.ProductImage]:
    return (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.position)
        .all()
    )


def get_public_product_images(
    product_id: int,
    db: Session,
) -> list[models.ProductImage]:
    _require_public_product(product_id, db)
    return _get_product_images(product_id, db)


def get_owned_product_images(
    product_id: int,
    user: models.User,
    db: Session,
) -> list[models.ProductImage]:
    _require_owned_product(product_id, user, db)
    return _get_product_images(product_id, db)
