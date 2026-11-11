from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.catalog import CatalogRequest
from ..services import catalog_service

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


def _catalog_response(catalog):
    return {
        "id": catalog.id,
        "name": catalog.name,
        "slug": catalog.slug,
        "user_id": catalog.user_id,
    }


@router.get("/{user_id}")
def get_catalog(user_id: int, db: Session = Depends(get_db)):
    catalog = catalog_service.get_catalog_by_user(user_id, db)
    return _catalog_response(catalog) if catalog else None


@router.post("")
def create_catalog(data: CatalogRequest, db: Session = Depends(get_db)):
    return _catalog_response(catalog_service.create_catalog(data, db))


@router.get("/public/{slug}")
def get_public_catalog(slug: str, db: Session = Depends(get_db)):
    catalog = catalog_service.get_public_catalog(slug, db)
    return {"id": catalog.id, "name": catalog.name, "slug": catalog.slug}
