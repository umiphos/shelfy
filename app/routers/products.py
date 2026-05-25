from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.catalog import Product, Business
from app.schemas import ProductCreate, ProductUpdate, ProductOut
from app.auth import get_current_business

router = APIRouter(prefix="/products", tags=["products"])


def get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def assert_ownership(product: Product, business: Business):
    if product.business_id != business.id:
        raise HTTPException(status_code=403, detail="Not your product")


# ── Private endpoints (require auth) ─────────────────────────────────────────

@router.post("/", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business),
):
    product = Product(**payload.model_dump(), business_id=current_business.id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/mine", response_model=List[ProductOut])
def list_my_products(
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business),
):
    return db.query(Product).filter(Product.business_id == current_business.id).all()


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business),
):
    product = get_product_or_404(product_id, db)
    assert_ownership(product, current_business)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}/toggle", response_model=ProductOut)
def toggle_availability(
    product_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business),
):
    """Quick toggle: available ↔ agotado. Ideal para el bot de WhatsApp."""
    product = get_product_or_404(product_id, db)
    assert_ownership(product, current_business)
    product.available = not product.available
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business),
):
    product = get_product_or_404(product_id, db)
    assert_ownership(product, current_business)
    db.delete(product)
    db.commit()
