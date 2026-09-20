from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from ..database import DbSession
from ..dependencies.auth import CurrentUser
from ..services import image_service

router = APIRouter(prefix="/api/products", tags=["product images"])


@router.post("/{product_id}/images")
async def upload_product_image(
    product_id: int,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File()],
    db: DbSession,
):
    image = await image_service.save_product_image(product_id, file, current_user, db)
    return {
        "id": image.id,
        "product_id": image.product_id,
        "filename": image.filename,
        "position": image.position,
        "url": f"/uploads/products/{image.filename}",
    }


@router.get("/public/{product_id}/images")
def get_public_product_images(product_id: int, db: DbSession):
    images = image_service.get_public_product_images(product_id, db)
    return _image_response(images)


@router.get("/{product_id}/images")
def get_product_images(
    product_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    images = image_service.get_owned_product_images(product_id, current_user, db)
    return _image_response(images)


def _image_response(images):
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
def delete_product_image(
    image_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    image_service.delete_product_image(image_id, current_user, db)
    return {"message": "Imagen eliminada"}
