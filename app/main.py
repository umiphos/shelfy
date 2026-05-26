from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth_router, products_router, catalog_router, bot_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Catalog API",
    description="API para catálogos de negocios locales. Actualizable vía WhatsApp bot.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(catalog_router)
app.include_router(bot_router)


@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
