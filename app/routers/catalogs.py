from fastapi import APIRouter

from ..database import DbSession
from ..dependencies.auth import CurrentUser
from ..schemas.catalog import CatalogRequest
from ..services import catalog_service, product_service

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


def _catalog_response(catalog):
    return {
        "id": catalog.id,
        "name": catalog.name,
        "slug": catalog.slug,
        "user_id": catalog.user_id,
    }


@router.get("/me")
def get_catalog(current_user: CurrentUser, db: DbSession):
    catalog = catalog_service.get_catalog_by_user(current_user, db)
    return _catalog_response(catalog) if catalog else None


@router.post("")
def create_catalog(
    data: CatalogRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    return _catalog_response(catalog_service.create_catalog(data, current_user, db))


@router.get("/public/{slug}")
def get_public_catalog(slug: str, db: DbSession):
    catalog = catalog_service.get_public_catalog(slug, db)
    return {"id": catalog.id, "name": catalog.name, "slug": catalog.slug}


@router.get("/public/{slug}/products")
def get_public_catalog_products(slug: str, db: DbSession):
    catalog = catalog_service.get_public_catalog(slug, db)
    return product_service.get_public_products(catalog.id, db)
