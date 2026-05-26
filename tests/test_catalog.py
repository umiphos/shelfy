"""
Tests para Catalog API
Run: pytest tests/ -v
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_business(name="Tacos Mary", email="mary@test.com", password="secret123"):
    return client.post("/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "whatsapp_number": "+523121234567",
    })


def get_token(email="mary@test.com", password="secret123"):
    r = client.post("/auth/login", data={"username": email, "password": password})
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_creates_business(self):
        r = register_business()
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "mary@test.com"
        assert data["slug"] == "tacos-mary"
        assert "hashed_password" not in data

    def test_register_duplicate_email_fails(self):
        register_business()
        r = register_business()
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]

    def test_login_returns_token(self):
        register_business()
        r = client.post("/auth/login", data={"username": "mary@test.com", "password": "secret123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password_fails(self):
        register_business()
        r = client.post("/auth/login", data={"username": "mary@test.com", "password": "wrong"})
        assert r.status_code == 401

    def test_weak_password_rejected(self):
        r = client.post("/auth/register", json={
            "name": "Test", "email": "x@x.com", "password": "123"
        })
        assert r.status_code == 422


# ── Products Tests ────────────────────────────────────────────────────────────

class TestProducts:
    def setup_method(self):
        register_business()
        self.token = get_token()
        self.headers = auth_headers(self.token)

    def test_create_product(self):
        r = client.post("/products/", json={
            "name": "Taco de Canasta",
            "price": "15.00",
            "available": True,
            "category": "tacos",
        }, headers=self.headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Taco de Canasta"
        assert float(data["price"]) == 15.0

    def test_price_must_be_positive(self):
        r = client.post("/products/", json={
            "name": "Taco gratis", "price": "-5.00"
        }, headers=self.headers)
        assert r.status_code == 422

    def test_list_my_products(self):
        client.post("/products/", json={"name": "Taco", "price": "15"}, headers=self.headers)
        client.post("/products/", json={"name": "Agua", "price": "10"}, headers=self.headers)
        r = client.get("/products/mine", headers=self.headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_update_product(self):
        create_r = client.post("/products/", json={"name": "Taco", "price": "15"}, headers=self.headers)
        pid = create_r.json()["id"]
        r = client.put(f"/products/{pid}", json={"price": "20.00"}, headers=self.headers)
        assert r.status_code == 200
        assert float(r.json()["price"]) == 20.0

    def test_toggle_availability(self):
        create_r = client.post("/products/", json={"name": "Taco", "price": "15", "available": True}, headers=self.headers)
        pid = create_r.json()["id"]
        r = client.patch(f"/products/{pid}/toggle", headers=self.headers)
        assert r.json()["available"] == False
        r2 = client.patch(f"/products/{pid}/toggle", headers=self.headers)
        assert r2.json()["available"] == True

    def test_cannot_edit_other_business_product(self):
        # Segundo negocio
        register_business("Otro", "otro@test.com")
        token2 = get_token("otro@test.com")
        headers2 = auth_headers(token2)

        # Mary crea producto
        create_r = client.post("/products/", json={"name": "Taco", "price": "15"}, headers=self.headers)
        pid = create_r.json()["id"]

        # Otro intenta editar — debe fallar
        r = client.put(f"/products/{pid}", json={"price": "1.00"}, headers=headers2)
        assert r.status_code == 403

    def test_delete_product(self):
        create_r = client.post("/products/", json={"name": "Taco", "price": "15"}, headers=self.headers)
        pid = create_r.json()["id"]
        r = client.delete(f"/products/{pid}", headers=self.headers)
        assert r.status_code == 204


# ── Catalog Public Tests ──────────────────────────────────────────────────────

class TestCatalog:
    def setup_method(self):
        register_business()
        self.token = get_token()
        self.headers = auth_headers(self.token)
        # Agregar productos
        client.post("/products/", json={"name": "Taco", "price": "15", "category": "tacos", "available": True}, headers=self.headers)
        client.post("/products/", json={"name": "Agua", "price": "10", "category": "bebidas", "available": False}, headers=self.headers)

    def test_public_catalog_accessible_without_auth(self):
        r = client.get("/catalog/tacos-mary")
        assert r.status_code == 200
        assert r.json()["slug"] == "tacos-mary"

    def test_catalog_not_found(self):
        r = client.get("/catalog/no-existe")
        assert r.status_code == 404

    def test_filter_available_only(self):
        r = client.get("/catalog/tacos-mary/products?available_only=true")
        products = r.json()
        assert all(p["available"] for p in products)
        assert len(products) == 1

    def test_filter_by_category(self):
        r = client.get("/catalog/tacos-mary/products?category=bebidas")
        products = r.json()
        assert all(p["category"] == "bebidas" for p in products)
