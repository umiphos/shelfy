import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.catalog import Business
from app.schemas import BusinessCreate, BusinessOut, Token
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


def unique_slug(db: Session, base_slug: str) -> str:
    slug = base_slug
    counter = 1
    while db.query(Business).filter(Business.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@router.post("/register", response_model=BusinessOut, status_code=201)
def register(payload: BusinessCreate, db: Session = Depends(get_db)):
    # Check duplicate email
    if db.query(Business).filter(Business.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate slug
    base_slug = slugify(payload.slug or payload.name)
    slug = unique_slug(db, base_slug)

    business = Business(
        name=payload.name,
        slug=slug,
        description=payload.description,
        whatsapp_number=payload.whatsapp_number,
        logo_url=payload.logo_url,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.email == form.username).first()
    if not business or not verify_password(form.password, business.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(business.id)})
    return {"access_token": token, "token_type": "bearer"}
