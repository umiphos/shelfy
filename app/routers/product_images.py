from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import image_service

router = APIRouter(prefix="/api/products", tags=["product images"])


@router.post("/{product_id}/images")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    image = await image_service.save_product_image(product_id, file, db)
    return {
        "id": image.id,
        "product_id": image.product_id,
        "filename": image.filename,
        "position": image.position,
        "url": f"/uploads/products/{image.filename}",
    }


@router.get("/{product_id}/images")
def get_product_images(product_id: int, db: Session = Depends(get_db)):
    images = image_service.get_product_images(product_id, db)
    return [
        {
            "id": image.id,
            "filename": image.filename,
            "position": image.position,
            "url": f"/uploads/products/{image.filename}",
        }
        for image in images
    ]


@router.delete("/images/{image_id}")
def delete_product_image(image_id: int, db: Session = Depends(get_db)):
    image_service.delete_product_image(image_id, db)
    return {"message": "Imagen eliminada"}
