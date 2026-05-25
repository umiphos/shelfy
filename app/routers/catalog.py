from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.catalog import Business, Product
from app.schemas import BusinessPublic, ProductOut

router = APIRouter(prefix="/catalog", tags=["catalog (public)"])


@router.get("/{slug}", response_model=BusinessPublic)
def get_catalog(slug: str, db: Session = Depends(get_db)):
    """
    Catálogo público de un negocio.
    URL: /catalog/maria-tortillas
    """
    business = db.query(Business).filter(
        Business.slug == slug,
        Business.is_active == True,
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return business


@router.get("/{slug}/products", response_model=List[ProductOut])
def get_catalog_products(
    slug: str,
    category: Optional[str] = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    Productos públicos con filtros opcionales.
    ?category=tacos&available_only=true
    """
    business = db.query(Business).filter(
        Business.slug == slug,
        Business.is_active == True,
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Catalog not found")

    query = db.query(Product).filter(Product.business_id == business.id)

    if available_only:
        query = query.filter(Product.available == True)
    if category:
        query = query.filter(Product.category == category)

    return query.order_by(Product.category, Product.name).all()
