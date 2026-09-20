def product_payload(status: str = "available") -> dict:
    return {
        "name": "Producto de prueba",
        "price": 100,
        "category_id": 1,
        "quantity": 2,
        "status": status,
    }


def create_catalog_and_product(client, authenticate_as, subject: str) -> int:
    authenticate_as(subject)
    catalog_response = client.post("/api/catalogs", json={"name": "Mi catálogo"})
    assert catalog_response.status_code == 200
    product_response = client.post("/api/products", json=product_payload())
    assert product_response.status_code == 200
    return product_response.json()["id"]


def test_private_routes_require_authentication(client):
    response = client.get("/api/catalogs/me")
    assert response.status_code == 401


def test_user_cannot_read_or_modify_another_users_product(
    client,
    authenticate_as,
):
    product_id = create_catalog_and_product(client, authenticate_as, "auth0|owner")

    authenticate_as("auth0|other")
    assert client.get(f"/api/products/{product_id}").status_code == 404
    assert (
        client.put(f"/api/products/{product_id}", json=product_payload()).status_code
        == 404
    )
    assert client.delete(f"/api/products/{product_id}").status_code == 404


def test_hidden_product_is_not_public(client, authenticate_as):
    authenticate_as("auth0|owner")
    client.post("/api/catalogs", json={"name": "Catálogo privado"})
    response = client.post("/api/products", json=product_payload(status="hidden"))
    product_id = response.json()["id"]

    assert client.get(f"/api/products/public/{product_id}").status_code == 404
    public_products = client.get("/api/catalogs/public/catalogo-privado/products")
    assert public_products.status_code == 200
    assert public_products.json() == []


def test_owner_identity_is_taken_from_token(client, authenticate_as):
    authenticate_as("auth0|owner")
    catalog = client.post("/api/catalogs", json={"name": "Catálogo seguro"})
    assert catalog.status_code == 200

    authenticate_as("auth0|other")
    assert client.get("/api/catalogs/me").json() is None
