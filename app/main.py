from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models
from .core.config import settings
from .database import Base, SessionLocal, engine
from .routers import auth, catalogs, categories, health, product_images, products


def ensure_default_category() -> None:
    with SessionLocal() as db:
        category = (
            db.query(models.Category)
            .filter(models.Category.name == "General / Otros")
            .first()
        )
        if not category:
            db.add(models.Category(name="General / Otros", active=True))
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings.product_upload_dir.mkdir(parents=True, exist_ok=True)
    ensure_default_category()
    yield


settings.product_upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_title, lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(catalogs.router)
app.include_router(products.router)
app.include_router(product_images.router)
app.include_router(categories.router)
