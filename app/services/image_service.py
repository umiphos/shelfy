from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models
from ..core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGES_PER_PRODUCT = 5


def delete_image_file(filename: str) -> None:
    filepath = settings.product_upload_dir / filename
    if filepath.exists():
        filepath.unlink()


async def save_product_image(
    product_id: int,
    file: UploadFile,
    db: Session,
) -> models.ProductImage:
    if not db.query(models.Product).filter(models.Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")

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


def delete_product_image(image_id: int, db: Session) -> None:
    image = (
        db.query(models.ProductImage).filter(models.ProductImage.id == image_id).first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    delete_image_file(image.filename)
    db.delete(image)
    db.commit()


def get_product_images(product_id: int, db: Session) -> list[models.ProductImage]:
    return (
        db.query(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
        .order_by(models.ProductImage.position)
        .all()
    )
