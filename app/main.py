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

Base.metadata.create_all(bind=engine)


app = FastAPI(title="CATÁLOGO API")
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
    category: str
    quantity: int
    description: str | None = None
    characteristics: str | None = None
    color: str | None = None
    size: str | None = None
    shipping: bool = False
    whatsapp: str | None = None

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
        .filter(models.Catalog.user_id == data.user_id)
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

    catalog = models.Catalog(
        name=name,
        user_id=data.user_id,
    )

    db.add(catalog)
    db.commit()
    db.refresh(catalog)

    return {
        "id": catalog.id,
        "name": catalog.name,
        "user_id": catalog.user_id,
    }

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

    if data.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad no puede ser negativa",
        )

    product = models.Product(
        catalog_id=data.catalog_id,
        name=data.name.strip(),
        price=data.price,
        category=data.category.strip(),
        quantity=data.quantity,
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

    if data.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad no puede ser negativa",
        )

    product.name = data.name.strip()
    product.price = data.price
    product.category = data.category.strip()
    product.quantity = data.quantity
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