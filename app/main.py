import bcrypt

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine
from pathlib import Path

from fastapi import File, UploadFile
from fastapi.staticfiles import StaticFiles

import os
import re
import unicodedata

Base.metadata.create_all(bind=engine)


def ensure_default_category():
    db = SessionLocal()

    try:
        category = (
            db.query(models.Category)
            .filter(
                models.Category.name == "General / Otros"
            )
            .first()
        )

        if not category:
            category = models.Category(
                name="General / Otros",
                active=True,
            )

            db.add(category)
            db.commit()
    finally:
        db.close()


ensure_default_category()

app = FastAPI(title="CATÁLOGO API")
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

cors_origins = [
    origin.strip()
    for origin in CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CatalogRequest(BaseModel):
    name: str
    user_id: int

class ProductRequest(BaseModel):
    catalog_id: int
    name: str
    price: float
    category_id: int
    quantity: int
    status: str = "available"
    description: str | None = None
    characteristics: str | None = None
    color: str | None = None
    size: str | None = None
    shipping: bool = False
    whatsapp: str | None = None

class CategoryRequest(BaseModel):
    name: str

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "CATÁLOGO API funcionando"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/api/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado",
        )

    hashed_password = bcrypt.hashpw(
        data.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    user = models.User(
        email=data.email,
        password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Usuario creado",
        "id": user.id,
        "email": user.email,
    }


@app.post("/api/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    password_valid = bcrypt.checkpw(
        data.password.encode("utf-8"),
        user.password.encode("utf-8"),
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    return {
        "message": "Login correcto",
        "id": user.id,
        "email": user.email,
    }


@app.get("/api/catalogs/{user_id}")
def get_catalog(
    user_id: int,
    db: Session = Depends(get_db),
):
    catalog = (
        db.query(models.Catalog)
        .filter(models.Catalog.user_id == user_id)
        .first()
    )

    if not catalog:
        return None

    return {
        "id": catalog.id,
        "name": catalog.name,
        "slug": catalog.slug,
        "user_id": catalog.user_id,
    }


@app.post("/api/catalogs")
def create_catalog(
    data: CatalogRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.id == data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    existing_catalog = (
        db.query(models.Catalog)
        .filter(
            models.Catalog.user_id == data.user_id
        )
        .first()
    )

    if existing_catalog:
        raise HTTPException(
            status_code=400,
            detail="El usuario ya tiene un catálogo",
        )

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="El nombre del catálogo es obligatorio",
        )

    base_slug = generate_slug(name)

    if not base_slug:
        raise HTTPException(
            status_code=400,
            detail="El nombre del catálogo no permite generar una URL válida",
        )

    slug = base_slug
    counter = 2

    while (
        db.query(models.Catalog)
        .filter(models.Catalog.slug == slug)
        .first()
    ):
        slug = f"{base_slug}-{counter}"
        counter += 1

    catalog = models.Catalog(
        name=name,
        slug=slug,
        user_id=data.user_id,
    )

    db.add(catalog)
    db.commit()
    db.refresh(catalog)

    return {
        "id": catalog.id,
        "name": catalog.name,
        "slug": catalog.slug,
        "user_id": catalog.user_id,
    }


@app.get("/api/catalogs/public/{slug}")
def get_public_catalog(
    slug: str,
    db: Session = Depends(get_db),
):
    catalog = (
        db.query(models.Catalog)
        .filter(models.Catalog.slug == slug)
        .first()
    )

    if not catalog:
        raise HTTPException(
            status_code=404,
            detail="Catálogo no encontrado",
        )

    return {
        "id": catalog.id,
        "name": catalog.name,
        "slug": catalog.slug,
    }


def generate_slug(name: str) -> str:
    text = unicodedata.normalize(
        "NFKD",
        name,
    ).encode(
        "ascii",
        "ignore",
    ).decode(
        "ascii",
    )

    text = text.lower()
    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )
    text = text.strip("-")

    return text


@app.get("/api/products/{catalog_id}")
def get_products(
    catalog_id: int,
    db: Session = Depends(get_db),
):
    products = (
        db.query(models.Product)
        .filter(
            models.Product.catalog_id == catalog_id
        )
        .all()
    )

    return products


@app.post("/api/products")
def create_product(
    data: ProductRequest,
    db: Session = Depends(get_db),
):
    catalog = (
        db.query(models.Catalog)
        .filter(
            models.Catalog.id == data.catalog_id
        )
        .first()
    )

    if not catalog:
        raise HTTPException(
            status_code=404,
            detail="Catálogo no encontrado",
        )

    if data.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio debe ser mayor que cero",
        )

    if data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad debe ser mayor que cero",
        )

    if data.status not in {
        "available",
        "sold_out",
        "hidden",
    }:
        raise HTTPException(
            status_code=400,
            detail="Estado de producto no válido",
        )

    category = (
        db.query(models.Category)
        .filter(
            models.Category.id == data.category_id,
            models.Category.active == True,
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=400,
            detail="Categoría no válida",
        )

    product = models.Product(
        catalog_id=data.catalog_id,
        name=data.name.strip(),
        price=data.price,
        category_id=data.category_id,
        quantity=data.quantity,
        status=data.status,
        description=data.description,
        characteristics=data.characteristics,
        color=data.color,
        size=data.size,
        shipping=data.shipping,
        whatsapp=data.whatsapp,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@app.get("/api/products/item/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado",
        )

    return product


@app.put("/api/products/{product_id}")
def update_product(
    product_id: int,
    data: ProductRequest,
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado",
        )

    if data.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio debe ser mayor que cero",
        )

    if data.status not in {
        "available",
        "sold_out",
        "hidden",
    }:
        raise HTTPException(
            status_code=400,
            detail="Estado de producto no válido",
        )

    if data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad debe ser mayor que cero",
        )

    category = (
        db.query(models.Category)
        .filter(
            models.Category.id == data.category_id,
            models.Category.active == True,
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=400,
            detail="Categoría no válida",
        )

    product.name = data.name.strip()
    product.price = data.price
    product.category_id = data.category_id
    product.quantity = data.quantity
    product.status = data.status
    product.description = data.description
    product.characteristics = data.characteristics
    product.color = data.color
    product.size = data.size
    product.shipping = data.shipping
    product.whatsapp = data.whatsapp

    db.commit()
    db.refresh(product)

    return product


@app.delete("/api/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado",
        )

    images = (
        db.query(models.ProductImage)
        .filter(
            models.ProductImage.product_id == product_id
        )
        .all()
    )

    for image in images:
        filepath = UPLOAD_DIR / image.filename

        if filepath.exists():
            filepath.unlink()

        db.delete(image)

    db.delete(product)
    db.commit()

    return {
        "message": "Producto eliminado"
    }

@app.post("/api/products/{product_id}/images")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado",
        )

    image_count = (
        db.query(models.ProductImage)
        .filter(
            models.ProductImage.product_id == product_id
        )
        .count()
    )

    if image_count >= 5:
        raise HTTPException(
            status_code=400,
            detail="El producto permite máximo 5 imágenes",
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagen no permitido",
        )

    extension = Path(file.filename or "").suffix.lower()

    filename = (
        f"{product_id}_"
        f"{image_count + 1}"
        f"{extension}"
    )

    filepath = UPLOAD_DIR / filename

    contents = await file.read()

    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="La imagen no puede superar 2 MB",
        )

    filepath.write_bytes(contents)

    image = models.ProductImage(
        product_id=product_id,
        filename=filename,
        position=image_count,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "id": image.id,
        "product_id": image.product_id,
        "filename": image.filename,
        "position": image.position,
        "url": f"/uploads/products/{filename}",
    }


@app.get("/api/products/{product_id}/images")
def get_product_images(
    product_id: int,
    db: Session = Depends(get_db),
):
    images = (
        db.query(models.ProductImage)
        .filter(
            models.ProductImage.product_id == product_id
        )
        .order_by(models.ProductImage.position)
        .all()
    )

    return [
        {
            "id": image.id,
            "filename": image.filename,
            "position": image.position,
            "url": f"/uploads/products/{image.filename}",
        }
        for image in images
    ]


@app.delete("/api/products/images/{image_id}")
def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = (
        db.query(models.ProductImage)
        .filter(
            models.ProductImage.id == image_id
        )
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Imagen no encontrada",
        )

    filepath = UPLOAD_DIR / image.filename

    if filepath.exists():
        filepath.unlink()

    db.delete(image)
    db.commit()

    return {
        "message": "Imagen eliminada"
    }


@app.get("/api/categories")
def get_categories(
    db: Session = Depends(get_db),
):
    categories = (
        db.query(models.Category)
        .filter(models.Category.active == True)
        .order_by(models.Category.name)
        .all()
    )

    return categories


@app.post("/api/categories")
def create_category(
    data: CategoryRequest,
    db: Session = Depends(get_db),
):
    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="El nombre de la categoría es obligatorio",
        )

    existing_category = (
        db.query(models.Category)
        .filter(models.Category.name == name)
        .first()
    )

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="La categoría ya existe",
        )

    category = models.Category(
        name=name,
        active=True,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category