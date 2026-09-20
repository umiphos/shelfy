import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..schemas.catalog import CatalogRequest


def generate_slug(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def get_catalog_by_user(user: models.User, db: Session) -> models.Catalog | None:
    return db.query(models.Catalog).filter(models.Catalog.user_id == user.id).first()


def get_public_catalog(slug: str, db: Session) -> models.Catalog:
    catalog = db.query(models.Catalog).filter(models.Catalog.slug == slug).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    return catalog


def create_catalog(
    data: CatalogRequest,
    user: models.User,
    db: Session,
) -> models.Catalog:
    if get_catalog_by_user(user, db):
        raise HTTPException(status_code=400, detail="El usuario ya tiene un catálogo")

    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=400, detail="El nombre del catálogo es obligatorio"
        )

    base_slug = generate_slug(name)
    if not base_slug:
        raise HTTPException(
            status_code=400,
            detail="El nombre del catálogo no permite generar una URL válida",
        )

    slug = base_slug
    counter = 2
    while db.query(models.Catalog).filter(models.Catalog.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    catalog = models.Catalog(name=name, slug=slug, user_id=user.id)
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    return catalog
