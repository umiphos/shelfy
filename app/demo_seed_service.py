from dataclasses import dataclass
from html import escape
from pathlib import Path

from sqlalchemy.orm import Session

from .. import models

DEMO_USER_SUBJECT = "demo|precioinbox"
DEMO_CATALOG_SLUG = "dummy"


@dataclass(frozen=True)
class DemoProduct:
    name: str
    price: float
    category: str
    quantity: int
    status: str
    description: str
    characteristics: str
    color: str | None
    size: str | None
    shipping: bool
    accent: str


DEMO_PRODUCTS = (
    DemoProduct(
        name="Café artesanal de Colima",
        price=180,
        category="Alimentos y bebidas",
        quantity=18,
        status="available",
        description="Café tostado de producción local, listo para moler o preparar.",
        characteristics="Bolsa de 500 g",
        color=None,
        size="500 g",
        shipping=True,
        accent="#B85C38",
    ),
    DemoProduct(
        name="Miel pura multifloral",
        price=145,
        category="Alimentos y bebidas",
        quantity=12,
        status="available",
        description="Miel natural de apiarios locales, sin mezclas ni conservadores.",
        characteristics="Frasco de 350 ml",
        color=None,
        size="350 ml",
        shipping=True,
        accent="#D99B2B",
    ),
    DemoProduct(
        name="Taza de barro pintada a mano",
        price=220,
        category="Artesanías",
        quantity=6,
        status="available",
        description="Pieza artesanal decorada a mano; cada taza tiene variaciones únicas.",
        characteristics="Barro esmaltado",
        color="Terracota",
        size="350 ml",
        shipping=True,
        accent="#9C4A36",
    ),
    DemoProduct(
        name="Bolsa tejida artesanal",
        price=390,
        category="Artesanías",
        quantity=4,
        status="available",
        description="Bolsa ligera elaborada por manos artesanas con acabado reforzado.",
        characteristics="Tejido artesanal con asas",
        color="Natural",
        size="Mediana",
        shipping=True,
        accent="#3D7968",
    ),
    DemoProduct(
        name="Pan de plátano casero",
        price=95,
        category="Alimentos y bebidas",
        quantity=8,
        status="available",
        description="Pan suave preparado en pequeños lotes con plátano maduro.",
        characteristics="Pieza de 500 g",
        color=None,
        size="500 g",
        shipping=False,
        accent="#A96F3B",
    ),
    DemoProduct(
        name="Diseño de logotipo básico",
        price=900,
        category="Servicios",
        quantity=10,
        status="available",
        description="Propuesta de identidad visual para pequeños negocios y productores.",
        characteristics="Incluye dos propuestas y archivos digitales",
        color=None,
        size=None,
        shipping=False,
        accent="#3F5E8C",
    ),
)


def _get_or_create_category(name: str, db: Session) -> models.Category:
    category = db.query(models.Category).filter(models.Category.name == name).first()
    if category:
        category.active = True
        return category

    category = models.Category(name=name, active=True)
    db.add(category)
    db.flush()
    return category


def _get_or_create_demo_catalog(db: Session) -> models.Catalog:
    catalog = (
        db.query(models.Catalog)
        .filter(models.Catalog.slug == DEMO_CATALOG_SLUG)
        .first()
    )
    if catalog:
        return catalog

    user = (
        db.query(models.User)
        .filter(models.User.auth0_subject == DEMO_USER_SUBJECT)
        .first()
    )
    if not user:
        user = models.User(auth0_subject=DEMO_USER_SUBJECT)
        db.add(user)
        db.flush()

    catalog = models.Catalog(
        name="Mercado Colima — Catálogo de muestra",
        slug=DEMO_CATALOG_SLUG,
        user_id=user.id,
    )
    db.add(catalog)
    db.flush()
    return catalog


def _demo_image_svg(product: DemoProduct) -> str:
    name = escape(product.name)
    category = escape(product.category.upper())
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">
<rect width="1200" height="1200" fill="#F5F0E8"/>
<circle cx="600" cy="500" r="300" fill="{product.accent}" opacity="0.16"/>
<circle cx="600" cy="500" r="210" fill="{product.accent}" opacity="0.28"/>
<rect x="130" y="810" width="940" height="230" rx="46" fill="#18201D"/>
<text x="600" y="875" text-anchor="middle" fill="#F5F0E8" font-family="Arial, sans-serif" font-size="30" font-weight="700" letter-spacing="4">{category}</text>
<text x="600" y="955" text-anchor="middle" fill="#F5F0E8" font-family="Arial, sans-serif" font-size="45" font-weight="700">{name}</text>
<text x="600" y="1015" text-anchor="middle" fill="#F5F0E8" font-family="Arial, sans-serif" font-size="26" opacity="0.7">precioinbox.com</text>
</svg>
"""


def _ensure_demo_image(
    product: models.Product,
    definition: DemoProduct,
    upload_dir: Path,
    db: Session,
) -> None:
    filename = f"demo-product-{product.id}.svg"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_text(
        _demo_image_svg(definition),
        encoding="utf-8",
    )

    image = (
        db.query(models.ProductImage)
        .filter(
            models.ProductImage.product_id == product.id,
            models.ProductImage.filename == filename,
        )
        .first()
    )
    if not image:
        db.add(
            models.ProductImage(
                product_id=product.id,
                filename=filename,
                position=0,
            )
        )


def seed_demo_data(db: Session, product_upload_dir: Path) -> None:
    """Create or reconcile the public demo catalog without duplicating rows."""
    catalog = _get_or_create_demo_catalog(db)

    for definition in DEMO_PRODUCTS:
        category = _get_or_create_category(definition.category, db)
        product = (
            db.query(models.Product)
            .filter(
                models.Product.catalog_id == catalog.id,
                models.Product.name == definition.name,
            )
            .first()
        )
        values = {
            "price": definition.price,
            "category_id": category.id,
            "quantity": definition.quantity,
            "status": definition.status,
            "description": definition.description,
            "characteristics": definition.characteristics,
            "color": definition.color,
            "size": definition.size,
            "shipping": definition.shipping,
            "whatsapp": None,
        }
        if not product:
            product = models.Product(
                catalog_id=catalog.id,
                name=definition.name,
                **values,
            )
            db.add(product)
            db.flush()
        else:
            for field, value in values.items():
                setattr(product, field, value)

        _ensure_demo_image(product, definition, product_upload_dir, db)

    db.commit()
