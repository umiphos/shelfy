from conftest import TestingSessionLocal

from app import models
from app.services.demo_seed_service import DEMO_PRODUCTS, seed_demo_data


def test_demo_seed_is_complete_and_idempotent(tmp_path, database):
    with TestingSessionLocal() as db:
        seed_demo_data(db, tmp_path)
        seed_demo_data(db, tmp_path)

        catalog = db.query(models.Catalog).filter(models.Catalog.slug == "dummy").one()
        products = (
            db.query(models.Product)
            .filter(models.Product.catalog_id == catalog.id)
            .all()
        )
        images = db.query(models.ProductImage).all()

        assert catalog.name == "Mercado Colima — Catálogo de muestra"
        assert len(products) == len(DEMO_PRODUCTS)
        assert len(images) == len(DEMO_PRODUCTS)
        assert len(list(tmp_path.glob("demo-product-*.svg"))) == len(DEMO_PRODUCTS)
