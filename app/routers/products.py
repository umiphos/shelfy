from fastapi import APIRouter

from ..database import DbSession
from ..dependencies.auth import CurrentUser
from ..schemas.product import ProductRequest
from ..services import product_service

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_products(current_user: CurrentUser, db: DbSession):
    return product_service.get_owned_products(current_user, db)


@router.post("")
def create_product(
    data: ProductRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    return product_service.create_product(data, current_user, db)


@router.get("/public/{product_id}")
def get_public_product(product_id: int, db: DbSession):
    return product_service.get_public_product(product_id, db)


@router.get("/{product_id}")
def get_product(
    product_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    return product_service.get_owned_product(product_id, current_user, db)


@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    return product_service.update_product(product_id, data, current_user, db)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    product_service.delete_product(product_id, current_user, db)
    return {"message": "Producto eliminado"}
